## Why

The "Abrir Customer Portal" button on the Artist change form says "Abrir" (Open) but doesn't open anything — it creates a Stripe portal session, then shows the URL as escaped plain text in a Django message. The admin must manually copy-paste the URL into a browser. This is a UX mismatch: the label promises to open the portal, the action only delivers a text URL.

## What Changes

- The `open_portal` admin action redirects the browser directly to the Stripe Customer Portal URL instead of showing it in a success message.
- The action button opens the portal in a new browser tab (`target="_blank"`) via Unfold's `attrs` parameter, so the admin stays in the Django admin.
- The existing spec scenario "Open portal returns portal URL" is updated to reflect new-tab redirect behavior.
- The existing test `test_open_portal_returns_portal_url_in_message` is updated to assert redirect location, and a new assertion verifies the `target="_blank"` attribute on the action link.

## Capabilities

### Modified Capabilities

- `artist-subscription-actions`: The "Open customer portal action" requirement changes from "show URL in a success message" to "redirect to the portal URL in a new browser tab". No new capabilities are added; this is a behavioral refinement of an existing action.

## Impact

- `artworks/admin.py` — `open_portal` method: replace `messages.success` + redirect-to-changeform with `return redirect(session.url)` and add `attrs={"target": "_blank"}` to the `@action` decorator
- `subscriptions/tests.py` — update `test_open_portal_returns_portal_url_in_message` to assert a redirect to the portal URL instead of `assertContains` on a message; add assertion for `target="_blank"` on the open-portal action link
- `openspec/changes/portal-redirect/specs/artist-subscription-actions/spec.md` — delta spec updated the "Open portal returns portal URL" scenario to reflect new-tab redirect; main spec (`openspec/specs/artist-subscription-actions/spec.md`) will be updated at archive
