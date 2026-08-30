## 1. Update open_portal action

- [x] 1.1 In `artworks/admin.py`, modify `open_portal` to replace `messages.success` + `redirect(redirect_url)` with `return redirect(session.url)`
- [x] 1.2 Verify `stripe_client.create_billing_portal_session` already passes `return_url` (it does — confirmed in `subscriptions/services/stripe_client.py:58`)

## 2. Open in new browser tab

- [x] 2.1 Add `attrs={"target": "_blank"}` to the `@action` decorator on `open_portal` in `artworks/admin.py`
- [x] 2.2 Add `assertRegex` assertion in `test_change_view_shows_copy_button_when_link_exists` to verify the open-portal link renders with `target="_blank"`

## 3. Update test

- [x] 3.1 In `subscriptions/tests.py`, rename `test_open_portal_returns_portal_url_in_message` to `test_open_portal_redirects_to_portal_url`
- [x] 3.2 Change assertion from `assertContains(response, url)` to `assertEqual(response.status_code, 302)` + `assertEqual(response.url, "https://billing.stripe.com/p/session")`
- [x] 3.3 Remove `follow=True` from the request since the redirect is now external (not followable by test client)

## 4. Spec update (handled at archive)

- [x] 4.1 The delta spec at `specs/artist-subscription-actions/spec.md` already captures the redirect behavior. The main spec will be updated automatically when the change is archived.
