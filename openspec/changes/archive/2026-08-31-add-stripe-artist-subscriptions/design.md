# Design — Stripe Artist Subscriptions

## Context

The project is a Django 5.2 + DRF dashboard (`enredarte-dashboard`) for an art-discovery website. The public API (`/apis/artworks/`) is consumed by an external site to list artists, artworks and galleries. Today the only gating mechanism is `Artist.is_active` and the analogous booleans on `Artwork`, `Gallery`, etc. — all of which are managed manually from the Django Unfold admin by an operator.

There is no commercial gate. We need artists to be discoverable only while they hold an active paid subscription, paid through Stripe. Cancellation must be friendly (visible through the end of the paid period), payment failures must give a short grace period before disappearing, and reactivation must be automatic when a new payment succeeds. Operators need a way to send a Stripe Checkout Session link to any artist and to see everything in real time from the admin.

Existing helpers that this design reuses without modification:
- `BaseModel.is_active` is already wired to `ArtistViewSet.get_queryset()` and to artwork-related derived queries (`Artist.available_artworks`, `new_additions`, etc.) in `core/models.py:26-34` and `artworks/views.py:34-39`. Flipping the boolean is sufficient to remove the artist from every public-facing query.
- `django-solo` is installed (`settings.py:30`), ideal for a `BillingPlan` singleton edited in the admin.
- `TokenAuthentication` is configured for DRF (`settings.py:212`), so the admin-only endpoints can be locked down by reusing `IsAuthenticated` via DRF or by gating on admin-rights via Django's `request.user.is_staff`.
- The project lives in Spanish and English (`LANGUAGE_CODE = "es"`, `LANGUAGES = [("es","Español"),("en","English")]`).

## Goals / Non-Goals

**Goals**

- One Stripe subscription per `Artist`. When the subscription lapses (cancelled or unpaid past grace), the artist disappears from `/apis/artworks/artists/` automatically within seconds.
- Operator can generate / regenerate a payment Checkout Session link and share it (copy-paste from admin, optional email button).
- 3-day grace period after a payment failure before the artist stops appearing.
- Friendly cancellation: cancelling keeps the artist visible until the end of the current paid period.
- Reactivation is automatic when the next invoice succeeds (the same artist + same email resume the subscription).
- Webhook audit log of every Stripe event received, so any divergence can be traced.
- Manual "sync from Stripe" escape hatch per artist (re-fetch state from API) in case a webhook is missed.
- Webhook signature verification + idempotency at the edge.
- Out-of-band escalation paths: from the admin, the operator can open the Stripe-hosted Customer Portal for the artist (self-service cancel / update card / view invoices).

**Non-Goals**

- Multiple pricing tiers ("Básico" / "Premium"). The architecture allows adding a `Plan` model later without breaking the existing data, but we ship exactly one `BillingPlan` (django-solo) today.
- Free trial periods.
- Coupons / promo codes.
- Multi-currency. Single currency (`MXN` by default; configurable per `BillingPlan`).
- Storing refunds / disputes inside our app — those are visible in the Stripe Dashboard.
- Re-implementing the Stripe-hosted payment / portal UI in our own templates.
- Notification emails to artists from our app. Email is out of scope here; the operator will use the dashboard link copy-paste or the optional single "send by SMTP" button.

## Decisions

### Decision: Custom `ArtistSubscription` model + raw `stripe` SDK, NOT `dj-stripe`

**Choice.** Use the official `stripe` Python SDK and a hand-written `ArtistSubscription` model that mirrors only the four or five fields we need (`status`, `stripe_customer_id`, `stripe_subscription_id`, `current_period_end`, `cancel_at_period_end`, `customer_email`, `signup_url`, `signup_url_expires_at`, `raw_state`).

**Rationale.** `dj-stripe` mirrors ~15 Stripe objects into Django (Customer, Subscription, Plan, Product, Invoice, Charge, Refund, Dispute, Source, Card, WebhookEndpoint, Event, ...). For a project this size that is a 10× overhead in tables, model migrations and operational risk. `dj-stripe`'s own docs (`docs/usage/webhooks.md`) drive webhook processing through their own internal `WebhookEventTrigger` table — using it would require us to either use their internal status model (vendor lock-in) or ignore it (which negates the value of the package). Furthermore, the project already has `django-solo` which makes the singleton-Plan use case trivial without dj-stripe.

**Alternatives considered.**
- `dj-stripe` (full mirror) — rejected for dependency size and lock-in.
- Stripe-only via Stripe Connect / Stripe Issuing — out of scope, no multi-tenant need.
- DIY over Stripe’s REST API with `requests` — equivalent but the official SDK already handles auth, retries, pagination, and type hints; using it is lower friction.

### Decision: Stripe Checkout Sessions (per-artist) + Customer Portal (post-payment), NOT Payment Links

**Choice.** Each `Artist` has a `signup_url` field pointing at a freshly created Checkout Session; once paying, they have access to the Stripe-hosted Customer Portal for self-service cancellation.

**Rationale.** Payment Links are great for one fixed URL shared widely, but they have no first-class way to attach `artist_id` metadata that survives the round-trip to the webhook. With Checkout Sessions we set `metadata={"artist_id": "..."}` per session so the webhook handler can correlate the subscription back to our `Artist` row with no race conditions. The Customer Portal solves the "artist wants to cancel" problem without us building a UI.

**Alternatives considered.**
- Stripe Payment Link (reusable, no code, but blind to artist identity) — rejected because operator needs link regeneration and per-artist control.
- Custom-built subscription management page — rejected: re-implementing what Stripe gives us for free, and we cannot store the cards.
- Checkout Sessions + manual cancellation email only — rejected as worse UX; Customer Portal is one more endpoint and is the de-facto pattern.

### Decision: `Artist.is_active` driven by a single helper function called only from webhook handlers

**Choice.** A pure function `subscription_state.compute_is_active(subscription, artist=None) -> bool` is the single source of truth. Webhook handlers call it inside `transaction.atomic()` and persist the result to `Artist.is_active`. The `artist` argument is only used by the no-subscription branch, which returns the artist's current boolean unchanged.

**Rationale.** Centralized logic eliminates drift between event handlers. The helper returns `True` only for statuses that keep the artist visible (ACTIVE, PAST_DUE within grace, CANCELING) and `False` for everything else (PENDING, CANCELED, PAST_DUE past grace). Admin actions ("manual sync", etc.) exist only as callers of the same helper, so manual changes and webhook-driven changes cannot disagree.

**Alternatives considered.**
- Each webhook handler flipping `is_active` independently — rejected; this is exactly the kind of logic that drifts when a 7th event type is added.
- Model `save()` auto-deriving `is_active` — rejected; merges concerns, breaks when we ever set `is_active=False` for an unrelated reason.

### Decision: A `pending` (unpaid) link does NOT make the artist visible

**Choice.** `compute_is_active` maps `status="pending"` to `Artist.is_active=False`. An artist becomes visible on the public site only on the first successful payment (`customer.subscription.created` → `active`), or while inside the grace / friendly-cancellation windows.

**Rationale.** The commercial gate is "appearing is conditional on an active subscription". An artist whose operator has merely generated a Checkout link has not paid, so they must not appear yet. Operators retain full control for artists without a subscription row via the manual `is_active` toggle (the `None` branch returns it unchanged).

**Alternatives considered.**
- PENDING → visible (optimistic onboarding) — rejected: it would surface non-paying artists, contradicting the gate's purpose.

### Decision: Idempotency via `StripeEvent` unique `event_id`, NOT in-memory locking

**Choice.** Every webhook write begins by `INSERT`-ing a `StripeEvent` row keyed by `event_id`. If the row already exists, we return 200 immediately and skip processing. The database's unique index is the lock.

**Rationale.** Stripe retries failed webhooks for up to 3 days. Without idempotency, a single missed "200" would double-update `Artist.is_active`. An in-memory dedupe cache would not survive restarts. A unique constraint is also visible to the operator (admin can inspect), which is helpful for debugging.

**Alternatives considered.**
- Cache (Redis) dedupe — needs extra infrastructure; nothing else in this project uses Redis yet; out of scope.
- Stripe replay-API dedupe — possible but slower and introduces a Stripe API call on every event.

### Decision: Stripe events processed inside one `transaction.atomic()` block per event

**Choice.** One DB transaction wraps: `ArtistSubscription.upsert`, `Artist.is_active = compute()`, `StripeEvent.processed_at = now`. If anything raises, the whole transaction rolls back, leaving `Artist.is_active` untouched; the `StripeEvent` row outside the atomic block still records the error so we can debug. We re-raise so Django returns 500 — Stripe then retries automatically.

**Rationale.** A webhook handler that updates `ArtistSubscription` but crashes before flipping `is_active` would leave the DB inconsistent. A single transaction guarantees `subscription.status` and `artist.is_active` move together, or not at all.

### Decision: Friendly cancellation (status `CANCELING` keeps `is_active=True` until `current_period_end`)

**Choice.** When the artist cancels, Stripe fires `subscription.updated` with `cancel_at_period_end=True`. We mirror that as `status=CANCELING`. The webhook that fires on actual period-end (`subscription.deleted`) sets `status=CANCELED`, which flips `is_active=False`.

**Rationale.** Industry-standard UX. Artist who cancels today still gets the month they paid for.

### Decision: 3-day configurable grace period via `BillingPlan.grace_period_days`

**Choice.** The grace period is configurable in the admin via `BillingPlan.grace_period_days` (default `3`). A future background job (or a computed field in tests today) interprets `current_period_end + grace_period_days` for license of `PAST_DUE` → `CANCELED`.

**Rationale.** Minimum amount of automation — Stripe re-attempts invoices for ~3 days by default. We do not want a separate background job to start triggering cancellations today; first version relies on the next webhook to do the flip (e.g. the next `invoice.payment_failed` after a `subscription.updated` that pushes `status` past the grace moment). If we need deterministic behavior, a tiny management command `subscriptions/reconcile` can fix it later — out of scope for v1.

**Alternatives considered.**
- Cron / Celery beat job — infrastructure not present in project; deferred.
- Stripe Smart Retries + immediate cancellation on first failure — rejected: too punishing on transient card issues.

### Decision: New `subscriptions` app, isolated from `artworks`, with a thin service-layer wrapper around the Stripe SDK

**Choice.** Folder layout: `subscriptions/` with `models.py`, `services/stripe_client.py`, `services/subscription_state.py`, `webhooks.py`, `views.py`, `urls.py`, `apps.py`, `admin.py`, migrations. Only `services/stripe_client.py` imports the `stripe` SDK directly; webhooks and views consume the small surface area defined here.

**Rationale.** Encapsulates the SDK behind a small interface the rest of the codebase calls. Replaces "remember to add retry on stripe.Subscription.modify" scattered across call sites with a single method on the service. Easy to test (mock `stripe_client` only).

### Decision: `Artist.email` becomes mandatory (`null=False`)

**Choice.** Migration backfills existing rows by prompting the operator (or via a small data migration to `""` empty) and changes the field to required.

**Rationale.** Stripe uses customer email as the customer's identity for the URL the artist receives. Without email, we cannot usefully generate a Checkout Session link.

## Risks / Trade-offs

- **[Webhook arrival failure]** → Mitigation: Stripe retries for ~3 days; `StripeEvent` is the audit trail; per-artist "sync from Stripe" salvavidas from admin; a future management command (`subscriptions/reconcile`) could sweep stale states but is deferred.
- **[Clock skew between Stripe and our DB]** → The `subscription_state` helper uses Stripe's `current_period_end`. If Stripe's clock drifts, a `CANCELING` artist could become invisible up to a few seconds early/late. Acceptable for v1.
- **[Stripe Dashboard activity that bypasses webhooks]** (operator refunds from Stripe UI) → Out of scope. Visible in Stripe Dashboard; we do not block with webhooks for refunds/disputes.
- **[Data migration of `Artist.email` to required]** → Migration needs care for existing artists with no email. Mitigated by prompting the operator per-artist before deployment; a safety-migration sets `email=""` and the form blocks new actions until set.
- **[Spam / abuse of "open Customer Portal"]** → Mitigated by gating the admin-only endpoints behind `IsAdminUser`. No public self-service.
- **[Plan price changes in Stripe Dashboard]** → Mitigation: change `BillingPlan.stripe_price_id` in admin maps to the new Stripe price; future work to migrate active subscriptions is out of scope.
- **[Three-legged test problem]** → The `StripeEvent` unique constraint solves replay; we still need integration coverage with the Stripe CLI. Manual test instructions go in `docs/testing-stripe.md`.
- **[Webhook URL is not authenticated]** → The endpoint is the only one not behind `IsAuthenticated`. Security is the signature, NOT session or token. CSRF must be disabled for that route (`@csrf_exempt`).

## Migration Plan

1. Land the change behind a feature flag or with empty `BillingPlan` (`stripe_price_id=""`) so the app boots even without Stripe configured. Existing `Artist.is_active=True` continues to drive visibility, unaffected.
2. In the Stripe Dashboard, create the product and price; copy the `price_xxx` ID. Configure the webhook endpoint URL pointing at `https://<host>/webhooks/stripe/` and copy the signing secret.
3. Fill `BillingPlan.stripe_price_id`, `STRIPE_*` environment variables, deploy.
4. Backfill `Artist.email` for any artists that lack one (admin-side prompt or quick data fix). Apply migration that sets the field required.
5. In admin, for artists that should be paying, click "Generar link de suscripción", copy the URL into the email of choice, send.
6. Smoke test: subscribe a single test card, verify `Artist.is_active=True` (already), then cancel from Customer Portal, verify the artist remains visible until period end, then disappears.
7. Rollback: if something is wrong, revert the deployment. Until `BillingPlan.stripe_price_id` is set, the admin screens for subscription are not actionable; existing `is_active=True` path is unchanged.

## Open Questions

- ~~Confirm whether the operator sends the link by hand (copy-paste) or wants an SMTP button.~~ **Resolved**: copy-paste only in v1. The "Generar" / "Regenerar" links reuse the project's existing copy-to-clipboard pattern (`docs/django-image-copy-link.md`, `static/js/copy_clipboard.js`, the `copy_to_clipboard` cookie) so the Stripe Checkout Session URL is automatically written to the clipboard on the next admin page load — the operator pastes it into email, WhatsApp, or any other channel. Adding an in-app SMTP "Send to artist" button is a deliberate future feature; no SMTP infrastructure is introduced here.
- ~~Decide where the Customer Portal `return_url` points after the artist leaves the portal.~~ **Resolved**: a neutral public landing page `GET /subscriptions/portal-return/` ("Gracias por usar el portal de gestión." / "Thanks for using the management portal."), so an artist who just cancelled does not land on the "subscription active" success text. Not configurable per environment.
- ~~Define the sync-from-Stripe branch when a Stripe customer exists but has zero subscriptions.~~ **Resolved**: the local status is set to `canceled` (the artist holds no paying subscription → not visible on the public site). Documented in `docs/stripe-subscriptions.md`.
- Decide whether to add a per-Stripe-event display in admin (filterable list) — included as a basic list view; advanced filters are out of scope.
- Decide whether to add a manual "force is_active=True" operator action that ignores subscription state. Not in v1; the helper re-derives from `ArtistSubscription.status`, so any forced toggle could be reverted by the next webhook.
