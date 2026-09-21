## Context

`Artist` has a reverse OneToOne `subscription` (`ArtistSubscription`) carrying `payment_method` (`online` default / `cash`) and `status` (`pending`/`active`/`past_due`/`canceling`/`canceled`). Operators work from `ArtistAdmin` changelist (`artworks/admin.py:307`), which already annotates `_has_subscription` (`Exists`) and `_subscription_status` (`Subquery`) to render the `Suscripción` badge without per-row queries, plus `Exists`-based filters (`ArtistAvailableWorksFilter`, `HasRelatedFilter`). The badge shows status only, so cash vs Stripe is invisible, and no filter exposes `payment_method` on either admin. Constraint from the user: the new filter goes **first (top)** in `ArtistAdmin.list_filter`.

## Goals / Non-Goals

**Goals:**
- Filter artists by payment method (`En línea` / `Efectivo` / `Sin suscripción`) from the Artist changelist, positioned top.
- Identify the method at a glance by prefixing the existing badge (`Efectivo · Activa`), preserving status colors.
- Keep the changelist N+1-free (annotations only) and follow existing `Exists`/`Subquery` idioms.
- One-line consistency: `payment_method` filter on `ArtistSubscriptionAdmin`.

**Non-Goals:**
- No model, migration, status, or Stripe-flow changes; no new changelist column; no combined method×status matrix filter; no search/export changes.

## Decisions

**D1: Custom `SimpleListFilter` next to `ArtistAvailableWorksFilter` (not a direct `subscription__payment_method` field filter).**
Why: a reverse-OneToOne join filter drops no-subscription rows and composes poorly with the existing `Count` annotations; a custom filter gives Spanish labels and an explicit `Sin suscripción` branch. Alternative (field filter with `ChoicesFieldListFilter`) rejected — no clean "none" option, English-ish rendering.
Filter: `title="Método de pago"`, `parameter_name="payment_method"`, lookups `online→En línea`, `cash→Efectivo`, `none→Sin suscripción`; queryset via `Exists(ArtistSubscription.objects.filter(artist=OuterRef("pk"), payment_method=...))` and `~Exists(...)` for `none`, mirroring `artworks/admin.py:267-279`.

**D2: Filter placed first in `ArtistAdmin.list_filter`.**
Why: explicit operator request; payment method is now the primary triage axis (cash confirmation vs Stripe ops). Alternative (append at end) rejected per requirement. Order: `[ArtistPaymentMethodFilter, is_active, created_at, location, has_artworks, has_available]`.

**D3: Enrich badge instead of adding a column.**
Why: 7 columns already; prefix inside the existing pill (`Efectivo · {status}` / `En línea · {status}`) adds zero width and reuses the annotation pipeline. Same `_BADGE_STYLES` per status (no second color dimension). `Sin suscripción` muted path unchanged. Alternative (separate `display_payment_method` column) rejected as redundant width — reconsider if operators need sorting/export.

**D4: One extra `Subquery` annotation `_payment_method` in `get_queryset`, consumed by `subscription_badge_from_artist` with graceful fallback.**
Why: mirrors `_subscription_status`; keeps badge render query-free. Fallback (annotation absent → status-only label) keeps shell/tests that build bare rows working. Alternative (per-row `artist.subscription` access) rejected — N+1 on a 50-row page.

## Risks / Trade-offs

- [Risk] `?payment_method=` param shadows the model field name → confusion with `subscription__payment_method` lookups. Mitigation: document the param in spec + tests; keep the name (intuitive URL) rather than inventing `has_payment`.
- [Risk] Extra `Subquery` per row could regress changelist latency → Mitigation: same shape as existing status subquery (indexed `artist` OneToOne lookup, `[:1]`); covered by `admin-list-performance` query-count test.
- [Risk] Badge label length (`Cancelada, vigente hasta fin de período` + prefix) wraps on narrow screens → Mitigation: short prefix (`Efectivo ·` / `En línea ·`), no new colors; acceptable wrapping.
- [Trade-off] 3-way filter includes `none`; "cash" excludes no-row artists by design (method ≠ missing). Documented in spec scenarios.

## Migration Plan

No migration. Deploy = code only; rollback = revert. No data rewrite (existing rows already carry `payment_method`, default `online`).
