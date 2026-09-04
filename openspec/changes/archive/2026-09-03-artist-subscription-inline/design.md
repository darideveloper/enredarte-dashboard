## Context

`Artist` (`artworks/models.py:9`, extends `Person` → `BaseModel` → `TimeStampedModel`) has at most one `ArtistSubscription` (`subscriptions/models.py:180`, `OneToOneField(Artist, related_name="subscription")`). The subscription is a local mirror of minimal Stripe state (`status`, `stripe_customer_id`, `stripe_subscription_id`, `customer_email`, `current_period_end`, `cancel_at_period_end`, `signup_url`+`signup_url_expires_at`, `last_synced_at`, `raw_state`, `created_at/updated_at`) plus `status` `TextChoices` (`pending/active/past_due/canceling/canceled`). Operators currently see the subscription in two places: a compact badge column on `ArtistAdmin` changelist (`artworks/admin.py:369` via `subscriptions/admin_helpers.py:45` + `_has_subscription` annotation at `artworks/admin.py:322`) and a fully separate read-only `ArtistSubscriptionAdmin` (`subscriptions/admin.py:181`). To inspect Stripe truth on the most common support path ("is paid? where is the link?") the operator must leave the `Artist` change form and open a second changelist. The request is to surface the subscription **inline** inside the artist form, read-only, with all fields and data, integrated with `django-unfold`.

Constraints: Stripe is source of truth; `ArtistSubscription` must not be created/edited inline (only via `generate_link`/`regenerate_link`/`open_portal`/`sync_from_stripe` actions at `artworks/admin.py:394-550` and webhook handlers at `subscriptions/webhooks.py`). Admin is `django-unfold==0.77.1` (`UNFOLD` at `project/settings.py:230`, base `ModelAdminUnfoldBase` at `project/admin_base.py:28`). Django 5.2 inline semantics apply (`max_num=1` required for `OneToOne`). Stack: `python 3.12`, `Django 5.2.x`, `unfold 0.77`.

## Goals / Non-Goals

**Goals:**
- Render every `ArtistSubscription` displayable field inside `ArtistAdmin` change form as a read-only `StackedInline` card, with Unfold styling, no editable inputs, and a link back to the standalone subscription admin.
- Render `status` as a colored badge (same palette as `subscription_badge`), `signup_url` as a clickable + copyable link with expiry awareness (copy affordance only when non-expired; "(expirado)" when past or empty), and `raw_state` as pretty JSON in a scrollable `<pre>` final trailing flat field titled "Auditoría" (no fieldsets).
- Handle the empty state gracefully ("Sin suscripción — usa 'Generar link de suscripción' arriba." muted message) when the artist has no subscription row.
- Preserve existing `ArtistAdmin` inlines (`ArtistTranslationInline`, `ArtistSocialLinkInline`) and actions; keep `ArtistSubscriptionAdmin` registered for search/filter/debug.
- Avoid N+1 and extra migrations; keep change as presentation-only.

**Non-Goals:**
- No schema change, no new model, no write path through the inline form (no create/edit/delete via inline).
- No change to Stripe flow, webhook handling, `compute_is_active`, or public API visibility (`GET /apis/artworks/artists/` filters on `Artist.is_active`).
- No `TabularInline`, no `raw_state` editable textarea, no `artist` FK field duplicated inline.

## Decisions

### Decision 1 — `unfold.admin.StackedInline` (not `admin.TabularInline`) with read-only semantics

**Choice:** Define `ArtistSubscriptionInline(StackedInline)` from `unfold.admin`, `model=ArtistSubscription`, `fk_name="artist"`, `extra=0`, `max_num=1`, `min_num=0`, `can_delete=False`, `show_change_link=True`, `fields` = explicit ordered list of all displayable fields plus 3 custom display methods, `readonly_fields = fields`, `has_add_permission→False`, `has_delete_permission→False`, appended to `ArtistAdmin.inlines`.

**Rationale:** `ArtistSubscription` has 12 displayable columns plus `raw_state` JSON — vertical card (stacked) is the only readable layout. All translation inlines in `artworks/admin.py:104` are `StackedInline`; billing read-only precedent `BillingPlanPriceHistoryInline:47` proves `extra=0/can_delete=False/has_add→False/readonly_fields=all` works for mirror data. `max_num=1` is required for `OneToOne`; without it Django surfaces `IntegrityError` instead of form validation. `show_change_link` uses the existing Unfold helper at `unfold/helpers/edit_inline/inline_links.html:5`.

**Alternatives considered:**
- `admin.TabularInline` — rejected: 12 columns overflow, poor a11y, JSON unreadable.
- Plain `django.contrib.admin.StackedInline` — rejected: bypasses Unfold card/`<details>` styling inherited via `BaseInlineMixin` (`unfold/admin.py:257`).
- Inline without `fk_name` — rejected: auto-detection works for single FK but explicit `fk_name="artist"` prevents `admin.E202` and documents intent.

### Decision 2 — All fields via `readonly_fields` + 3 `display_*` methods, ordered flat fields (no fieldsets)

**Choice:** Omit the redundant `artist` FK from `fields` (parent is known). Render 12 fields as an ordered flat `fields` list plus 3 custom display methods:

- `display_status` (`@admin.display(description="Estado")` → `subscription_badge(obj)`) — replaces raw `status` choice value with the same amber/green/red palette at `subscriptions/admin_helpers.py:7`.
- `display_signup_url` (`@admin.display(description="Link de pago")`) → `format_html('<a href="{url}" target="_blank">{url}</a><span data-copy-url="{url}">')` with expiry check via `_link_is_valid` (`signup_url` present and `signup_url_expires_at` not past; "past or empty" → "(expirado)"); copy affordance (`data-copy-url`) only when valid, matching `copy_clipboard.js`.
- `display_raw_state` (`@admin.display(description="Auditoría")`) → `json.dumps(obj.raw_state, indent=2, ensure_ascii=False)` wrapped in `<pre style="max-height:320px;overflow:auto">`; placed as the final trailing flat field (no `fieldsets`/collapse, ordered by `fields`).

Order: `display_status`, `stripe_customer_id`, `stripe_subscription_id`, `customer_email`, `current_period_end`, `cancel_at_period_end`, `display_signup_url`, `signup_url_expires_at`, `last_synced_at`, `created_at`, `updated_at`, `display_raw_state`.

**Rationale:** `ArtistSubscriptionAdmin.readonly_fields:201` is the source of truth for which fields are safe to expose. Reusing the same set ensures completeness. `signup_url` as plain text is not operator-friendly; `raw_state` as `str(dict)` is noisy — custom display matches `subscription-admin-controls` success/cancel/portal-return copy patterns. Flat `fields` is the proven pattern in this repo (all 10 translation inlines and `ArtistSocialLinkInline` use `fields`, zero inlines use `fieldsets`); Unfold's `edit_inline/stacked.html` flattens `fieldsets` unpredictably, so an ordered flat list is the YAGNI, best-practice choice (confirmed by user decision 2026-09-03).

**Alternatives considered:**
- `fieldsets` with `classes: ("collapse",)` — rejected: unproven in this repo, requires manual verification of Unfold flattening, adds nesting without benefit for 12 fields.
- Showing raw `status` charfield — rejected: loses badge UX that operators already rely on in changelist.

### Decision 3 — Empty state via inline template override (not formset hack)

**Choice:** Provide a minimal template `templates/admin/subscriptions/artistsubscription/edit_inline/stacked.html` extending `unfold`'s stacked template, rendering `<p style="color:#6b7280">Sin suscripción — usa "Generar link de suscripción" arriba.</p>` when `inline_admin_formset.formset.queryset|length==0 and inline_admin_formset.formset.extra==0`. Set `ArtistSubscriptionInline.template` to it.

**Rationale:** Django's `extra=0` with 0 objects yields 0 forms and only the header — the user sees an empty card with no affordance. A formset hack (forcing `extra=1` dummy readonly form) violates `max_num=1` + `has_add→False`. A small template is canonical and keeps the existing changelist badge (`artworks/admin.py:369`) as secondary signal.

**Alternatives considered:**
- Relying solely on `ArtistAdmin.change_view:270` `copy_button_extra_attrs` / badge for empty signal — rejected: inline header would still look broken.
- Inline `get_queryset` returning a placeholder unsaved instance — rejected: submits to DB on save.

### Decision 4 — Location of the inline class

**Choice:** Define `ArtistSubscriptionInline` definitively in `artworks/admin.py` (next to `ArtistAdmin`) importing `ArtistSubscription` from `subscriptions.models`, importing `subscription_badge` from `subscriptions/admin_helpers.py`. Placement in `subscriptions/admin.py` with import into `artworks/admin.py` is rejected due to circular-import risk (`artworks/admin.py` already imports `BillingPlan` from `subscriptions/models`).

### Decision 5 — Keep standalone `ArtistSubscriptionAdmin` + `show_change_link`

**Choice:** Do not unregister `ArtistSubscriptionAdmin`. The inline is the **convenience view**; the standalone admin remains the debug/search view (`search_fields: artist__name/email, stripe_*_id`, `list_filter: status/artist_is_active`). `show_change_link=True` lets the inline footer link to the full row for payload inspection.

## Risks / Trade-offs

- **Write bypass via crafted POST** → Mitigation: `readonly_fields = fields` (Django excludes from `cleaned_data`/`form.fields`) + `has_add_permission=False` + `has_delete_permission=False` + `can_delete=False`. No writable field remains to CREATE via inline.
- **`has_change_permission=False` hides inline (Django 5.2)** → Mitigation: Keep `has_change True` (or explicitly `has_view_permission True`); read-only semantics already block mutation.
- **Flat `fields` ordering chosen over `fieldsets`** → Mitigation: Flat `fields` is proven in this repo (all translation inlines use `fields`); avoids Unfold `edit_inline/stacked.html` flattening uncertainty that would require manual verification of `fieldsets`.
- **`raw_state` large JSON bloats change-form HTML** → Mitigation: Trailing `display_raw_state` field with `<pre style="max-height:320px;overflow:auto">` scroll + collapsed visual grouping by ordering; full payload also reachable via `show_change_link` standalone admin detail.
- **One extra query per change form** (`ArtistSubscription.objects.filter(artist=pk)`) → Mitigation: Acceptable; changelist already annotates via `Exists`/`Subquery` — change view not paginated. Optionally `select_related("subscription")` in `ArtistAdmin.get_queryset`.
- **Tests brittle on `inlines` order** (`artworks/tests.py:91` asserts `assertIn(ArtistTranslationInline, inlines)`) → Mitigation: Update tests to assert set membership, not positional equality.
- **Circular import if inline placed in `subscriptions/admin.py`** → Mitigation: Definitive location is `artworks/admin.py`; importing `ArtistSubscription` there is already done for `BillingPlan`, no cycle.
- **Unfold template path for empty state** (`templates/admin/subscriptions/artistsubscription/edit_inline/stacked.html`) → Mitigation: Verify Unfold's `StackedInline` template override path (Unfold's `edit_inline/stacked.html` vs `unfold` helper) in 0.77.1; add fallback note to keep changelist badge "Sin suscripción" as secondary signal if override path differs.

## Migration Plan

1. Add `ArtistSubscriptionInline` + append to `ArtistAdmin.inlines` (no migration).
2. Add empty-state inline template if chosen.
3. Update `artworks/tests.py` inline assertions; add tests for read-only rendering, empty state, and `show_change_link` presence.
4. Deploy — no data backfill, no Stripe interaction.
5. Rollback: revert `ArtistAdmin.inlines` entry + remove inline class/template; no DB change.

## Open Questions

*None — resolved 2026-09-03:*

- **Raw state display:** Pretty-printed `<pre>` inline (final trailing field) **plus** `show_change_link` to standalone admin detail (user decision "Suscripción + pretty JSON").
- **Inline title:** Singular Spanish `"Suscripción"` (per `AGENTS.md` Spanish literals and `subscriptions/models.py:261` `verbose_name="Suscripción de artista"`); `"Suscripción Stripe"` not used.
- **Field grouping:** Ordered flat `fields` (not `fieldsets`) per user decision "Use plain flat fields".
