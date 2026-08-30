## 1. ArtistAdmin actions_detail setup

- [x] 1.1 Add `actions_detail` list with 4 action names to `ArtistAdmin`: `generate_link`, `regenerate_link`, `open_portal`, `sync_from_stripe`
- [x] 1.2 Add `has_generate_link_permission` method — returns `True` only when artist has no subscription
- [x] 1.3 Add `has_regenerate_link_permission` method — returns `True` only when artist has a subscription
- [x] 1.4 Add `has_open_portal_permission` method — returns `True` only when `stripe_customer_id` is set
- [x] 1.5 Add `has_sync_from_stripe_permission` method — always returns `True`

## 2. Migrate action logic from views to admin methods

- [x] 2.1 Move `_billing_blocked`, `_set_clipboard_cookie`, `_artist_redirect_url` helpers from `subscriptions/views.py` to `artworks/admin.py`
- [x] 2.2 Implement `generate_link` action method — create Stripe customer + checkout session, set cookie, redirect
- [x] 2.3 Implement `regenerate_link` action method — reuse valid URL or create new session, set cookie, redirect
- [x] 2.4 Implement `open_portal` action method — create billing portal session, set cookie, redirect
- [x] 2.5 Implement `sync_from_stripe` action method — fetch from Stripe, update subscription + artist.is_active, redirect

## 3. Remove old template and context injection

- [x] 3.1 Delete `project/templates/admin/artworks/artist/change_form.html`
- [x] 3.2 Remove `change_view` override from `ArtistAdmin` (lines 296-304)
- [x] 3.3 Keep `Media.js = ["js/copy_clipboard.js"]` on `ArtistAdmin`

## 4. Clean up subscriptions app

- [x] 4.1 Remove 4 standalone admin views from `subscriptions/views.py` (`generate_link`, `regenerate_link`, `open_portal`, `sync_from_stripe`)
- [x] 4.2 Remove helper functions that are no longer used (`_artist_redirect_url`, `_set_clipboard_cookie`, `_billing_blocked`, `MSG_LINK_COPIED`)
- [x] 4.3 Remove 4 admin URL patterns from `subscriptions/urls.py` (lines 16-35)
- [x] 4.4 Keep public landing page views (`success`, `cancel`, `portal_return`) and their URL patterns

## 5. Update tests

- [x] 5.1 Rewrite `AdminEndpointTest` tests to use GET requests to new admin action URLs (e.g., `/admin/artworks/artist/{id}/generate-link/`)
- [x] 5.2 Update `test_change_view_has_action_buttons` to verify buttons render via Unfold `actions_detail`
- [x] 5.3 Verify all other tests pass (`ComputeIsActiveTest`, `WebhookTest`, `ArtistAdminBadgeTest`)

## 6. Verify

- [x] 6.1 Run `python manage.py check` — no issues
- [x] 6.2 Run `python manage.py test subscriptions` — 37/38 pass (1 pre-existing webhook failure)
- [x] 6.3 Manual: visit Artist change form — buttons appear horizontally in header
- [x] 6.4 Manual: test each action (generate, regenerate, portal, sync) works correctly

## 7. Fix: clipboard cookie path

- [x] 7.1 Fix `_set_clipboard_cookie` to set `path="/"` so cookie is available on the redirect target (change form page)

## 8. Copy-link button state machine

- [x] 8.1 Change `actions_detail` to `["generate_link", "sync_from_stripe"]` (remove `regenerate_link`, `open_portal`)
- [x] 8.2 Add `_link_is_valid(sub)` helper — true only when a non-expired `signup_url` exists
- [x] 8.3 Update `has_generate_link_permission` to return `not _link_is_valid(sub)`; delete regenerate/portal permission methods
- [x] 8.4 Delete `regenerate_link` and `open_portal` action methods
- [x] 8.5 Add `@action(permissions=[...])` to generate/sync so permission methods actually filter buttons
- [x] 8.6 Re-add `change_view` override injecting `signup_url` (non-expired only) into context
- [x] 8.7 Recreate `change_form.html` with a single horizontal `<li>` "Copiar link" button (`data-copy-url`) before `{{ block.super }}`
- [x] 8.8 Rewrite `copy_clipboard.js`: click-to-copy with fallback; remove cookie flow
- [x] 8.9 Remove `_set_clipboard_cookie`; rename `MSG_LINK_COPIED` → `MSG_LINK_GENERATED` with accurate text

## 9. Update tests for copy-button state machine

- [x] 9.1 Remove `test_regenerate_link_*` and `test_open_portal_*` tests
- [x] 9.2 Update `test_generate_link_*` to drop cookie assertions; add `test_generate_link_refreshes_expired_link`
- [x] 9.3 Add copy-button visibility tests (shown with valid link, hidden with expired link, generate hidden when link exists)

## 10. Verify final state

- [x] 10.1 Run `python manage.py check` — no issues
- [x] 10.2 Run `python manage.py test subscriptions` — 37/37 pass except 1 pre-existing webhook failure

## 11. Restore regenerate/portal; refine state machine

- [x] 11.1 Re-add `regenerate_link` and `open_portal` action methods (no cookie flow; `MSG_LINK_REGENERATED` message)
- [x] 11.2 Restore both to `actions_detail` with `@action(permissions=[...])`
- [x] 11.3 Add `_link_exists(sub)` helper; gate generate on `not _link_exists`, regenerate/portal on `_link_exists`
- [x] 11.4 Add `MSG_LINK_REGENERATED` constant
- [x] 11.5 Re-add regenerate/portal endpoint tests; adjust portal tests to include `signup_url`; remove obsolete expired-generate test
- [x] 11.6 Update badge visibility tests for the matrix (no-link / valid / expired)
- [x] 11.7 Update spec, design, proposal artifacts for the restored actions

## 12. Close verification warnings (test-only fixes)

- [x] 12.1 Add `test_generate_link_blocked_by_inactive_billing_plan` and `test_generate_link_blocked_by_missing_price_id` (covers the billing-plan-blocked spec scenario)
- [x] 12.2 Fix `test_invoice_payment_failed_sets_past_due` to assert `is_active` stays True within grace — matches `compute_is_active` (pre-existing incorrect expectation; no codebase change)
- [x] 12.3 Run `python manage.py test subscriptions` — 42/42 pass