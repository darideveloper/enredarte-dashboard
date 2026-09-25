## Context

`ArtworkOrder` and its lifecycle live in `artworks/`, but every Stripe touchpoint for sales lives in `subscriptions/`: `create_artwork_checkout_session` / `retrieve_checkout_session` / `create_refund` (`stripe_client.py:124-166`), all `send_sale_*` senders + 36 `sale_*` templates, and the artwork branches of the single `POST /webhooks/stripe/` handler. The result is a two-way dependency: `artworks/views|services|commands|admin` import from `subscriptions.services`, while `subscriptions/webhooks.py` lazily imports from `artworks.models|services` to avoid a circular import. `StripeEvent` + `epoch_to_datetime` in `subscriptions/models.py` are shared by both flows but owned by one side. User decisions locked in explore: sales move to `artworks/`, shared primitives move out of `subscriptions/`, hard cut with no compat shims.

Constraints: single Stripe account + single webhook URL (dashboard-registered, must not split); shared Postgres across worktrees (migrate from one sibling at a time); canonical test runner `venv/bin/python manage.py test`; testing-contract bans pytest; `specs/email-notifications` currently mandates the single-mailer module (updated by this change's delta specs).

## Goals / Non-Goals

**Goals:**
- `artworks/` owns everything sale-shaped (Stripe order client, sale senders + templates, sale webhook logic); all sale modules import zero from `subscriptions`.
- `subscriptions/` owns membership-only code (plan, subscription state, cash/online mail, subscription webhook logic).
- Shared primitives (`StripeEvent`, `epoch_to_datetime`, `sget`/`to_plain_dict`, `core/stripe.py` SDK init, `send_best_effort`/per-audience renderer) owned by `core/` with no domain coupling.
- No behavior change: same URLs, metadata, subjects, bodies, throttles, lifecycle, idempotency, best-effort mail.

**Non-Goals:**
- No new Django app (`payments/` rejected — a third app for three helpers + one model is heavier than `core/` ownership; revisit if a second PSP arrives).
- No public API, email copy, subject, or Stripe metadata changes.
- No `BillingPlan` / `ArtistSubscription` / order lifecycle logic changes.
- **No relocation of artist-membership admin.** `artworks/admin.py` keeps importing `subscriptions.models`/`services` for the `ArtistSubscription` inline and the generate-link/portal/cash/sync actions. The zero-import rule applies to sale modules only; membership admin is legitimate cross-domain use and stays put.

## Decisions

**Decision 1: sales → flat modules in `artworks/`, not a `payments/` app.**
New modules `artworks/stripe_orders.py` (3 fns), `artworks/sale_notifications.py` (sale block), `artworks/order_webhooks.py` (sale branches as pure functions taking `order` + `session` dict). `artworks/services.py` already exists as a module and cannot coexist with an `artworks/services/` package, so the new files are flat siblings. Alternative `payments/` app considered: rejected per YAGNI — it would need `INSTALLED_APPS`, admin, its own tests home, and a second move of sale code out of it later. `artworks/` is where `ArtworkOrder` and its tests already live.
**Decision 2: shared primitives → `core/`, not `artworks/`.**
`StripeEvent` logs both flows so neither domain app is its correct home. `core/models.py` gains `StripeEvent` (identical fields); `core/stripe_utils.py` gains `epoch_to_datetime`; `subscriptions/services/stripe_compat.py` moves to `core/stripe_compat.py` (same two functions, all import sites updated, old module deleted — hard cut, no alias). Alternative `artworks/StripeEvent` rejected: it just swaps who is misplaced.
**Decision 3: webhook envelope stays, logic delegates.**
`subscriptions/webhooks.py` keeps signature verification + `StripeEvent` insert + atomic block + `HANDLERS` table shape, but artwork branches delegate to `artworks.order_webhooks`. Dispatch key stays `metadata.kind == "artwork_order"`. Alternative of splitting into two URLs rejected: requires Stripe dashboard rotation and doubles signature/idempotency surface for zero domain gain.
**Decision 4: hard cut, phased order, no shims.**
Move order: templates + senders (no DB) → order client (no DB) → webhook delegation (no DB) → shared primitives + data migration (only stateful step). Each phase moves source + all callers + mock strings together; `manage.py test` gates every phase. Alternative big-bang single commit rejected: ~43 mock paths + migration in one shot is unreviewable and unbisectable on shared DB.
**Decision 5: SDK init + shared mail plumbing live in one `core` module each.**
`core/stripe.py` sets `stripe.api_key`/`stripe.api_version` on import and owns the `STRIPE_*` presence check; `artworks/stripe_orders.py` and `subscriptions/services/stripe_client.py` both `import core.stripe` so any path that calls Stripe is authenticated (today only `stripe_client.py` init does this, and artwork-only commands/requests would not import it). `core/mail_utils.py` holds `send_best_effort` + the per-audience renderer, shared by `artworks/sale_notifications.py` and `subscriptions/services/notifications.py`. The renderer SHALL take the **full template base path** as an argument (today it hardcodes `subscriptions/email/`), so sale callers pass `artworks/email/sale_*` and online callers pass `subscriptions/email/*`; without this, moving the sale templates to `artworks/` would make every sale send raise `TemplateDoesNotExist`. Alternative (keep init only in `stripe_client.py`) rejected: it forces a cross-domain import from sale code or leaves a silent unauthenticated-Stripe failure mode.
**Decision 6: `StripeEvent` moves by copy, not by `db_table` rename.**
`core/0001_initial` creates `core_stripeevent`; the dependent `subscriptions` migration `bulk_create`s the historical rows into the new model, asserts count equality, then `DeleteModel`s the old one. `SeparateDatabaseAndState`/`ALTER TABLE RENAME` rejected: it would keep the `subscriptions_*` table name while the model lives in `core`, needing a permanent `db_table` override and leaving content-type state split — not worth it for a small audit table. The reverse migration is a guarded no-op (copies back only if the new table was not appended to).

## Risks / Trade-offs

- [Risk] `StripeEvent` data migration loses rows or breaks the `event_id` UNIQUE lock → Mitigation: **plain copy, not a table rename** (no `SeparateDatabaseAndState`, which complicates state/content-type handling for a small audit table). Mechanism, pinned: (1) `core/migrations/0001_initial.py` creates `core_stripeevent`; (2) a new `subscriptions` migration with `dependencies = [("core", "0001_initial"), ...]` runs `RunPython`: read the historical `apps.get_model("subscriptions", "StripeEvent")` rows, `bulk_create` them into `apps.get_model("core", "StripeEvent")` preserving `event_id`/`event_type`/`received_at`/`processed_at`/`payload`/`error`, assert `core.count() == subscriptions.count()`, then state `DeleteModel` the old model (reverse migration is a no-op that refuses if the new table has more rows). Verify counts before/after on a staging copy.
- [Risk] Shared-Postgres worktrees diverge (`enredarte` DB migrated from two siblings) → Mitigation: migrate from one sibling at a time per `AGENTS.md`; `DB_ENGINE=sqlite3` escape hatch documented.
- [Risk] Stripe SDK unauthenticated on artwork-only paths after the split → Mitigation: `core/stripe.py` initializes `stripe.api_key`/`api_version` on import and both `stripe_orders.py` and `stripe_client.py` import it; `artworks` management commands and `buy` therefore always set credentials before any Stripe call.
- [Risk] Hard-cut mock churn misses a string (`subscriptions.services.stripe_client.create_refund` is patched in 3 subscription tests; `artworks/tests.py` has 39 `subscriptions.services.stripe_client` refs) → Mitigation: grep for `subscriptions.services.(stripe_client|notifications)` sale names + `subscriptions/email/sale_` + `subscriptions.models import.*StripeEvent` must return zero hits at the end; tests gate each phase.
- [Risk] Template path rename breaks an out-of-repo override → Mitigation: repo-wide grep for `subscriptions/email/sale_` (only `notifications.py` references them today); no locale overrides reference sale templates.
- [Risk] Shared renderer's hardcoded `subscriptions/email/` prefix makes every moved sale send raise `TemplateDoesNotExist` → Mitigation: parameterize `core/mail_utils` renderer to take the full template base; sale callers pass `artworks/email/sale_*`, online callers `subscriptions/email/*`; add a render test per namespace.
- [Risk] `send_best_effort` rename touches 21 call sites across both apps → Mitigation: explicit task enumerating them; final grep must show zero `notifications.send_best_effort` remaining and all callers importing `core.mail_utils.send_best_effort`.
- [Risk] `core` modules log under `core.*` loggers not present in `LOGGING`, so best-effort failure logs only hit Python's `lastResort` handler → Mitigation: add a `"core"` logger entry (console handler, `INFO`, `propagate: False`) to `project/settings.py`.
- [Trade-off] `subscriptions/apps.py ready()` STRIPE_* boot gate stays in `subscriptions`; the shared `core/stripe.py` performs the presence check on import, so the gate stays meaningful even as `artworks` gains Stripe calls. Revisit if a second Stripe account appears.

## Migration Plan

1. Phase 1 (no DB): move templates + `artworks/sale_notifications.py`, `core/mail_utils.py`; rewrite callers + sale mail tests (`artworks/tests.py`). Gate: `manage.py test artworks subscriptions`.
2. Phase 2 (no DB): move `artworks/stripe_orders.py` + `core/stripe.py`; rewrite all mock paths incl. `subscriptions/tests.py` sale refund patches. Gate: full suite.
3. Phase 3 (no DB): extract `artworks/order_webhooks.py`, dispatcher delegates. Gate: webhook tests incl. double-delivery + double-sale refund.
4. Phase 4 (DB): `core` `StripeEvent` + `stripe_utils` + `stripe_compat` move + `core/0001_initial` + dependent subscriptions data migration; `StripeEventAdmin` registration moves to `core/admin.py`; update docs + `emails-track.md` + specs archive. Gate: full suite + `StripeEvent` row-count check.
5. Feature regression pass (no code): run the checklist in `tasks.md` group 6 against the test suite + manual Stripe CLI replay. Gate: every listed feature green.
6. Rollback: Phases 1-3 revert cleanly (no schema change). Phase 4 rolls back via reverse migration only before new events accumulate; after that, forward-fix.

## Open Questions

- Q1 (answered in explore, recorded): StripeEvent destination — `core/` (locked).
- Q2: Stripe SDK init + `STRIPE_*` presence check live in `core/stripe.py`, imported by both `artworks` and `subscriptions`; `subscriptions/apps.py` keeps its boot gate. Flag if a second Stripe account ever appears.
