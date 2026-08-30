## 1. Remove dead `add_tailwind_styles.js`

- [x] 1.1 Delete `static/js/add_tailwind_styles.js`
- [x] 1.2 Remove the `<script src="{% static 'js/add_tailwind_styles.js' %}">` line from `project/templates/admin/base.html`

## 2. Render copy buttons via the Unfold button component

- [x] 2.1 Update `ArtistAdmin.change_view` (`artworks/admin.py`) to inject `copy_button_extra_attrs` (a `mark_safe` string `type="button" data-copy-url="<url>"`) in place of the raw `signup_url` context key
- [x] 2.2 Update `project/templates/admin/artworks/artist/change_form.html` to render the copy button with `{% component "unfold/components/button.html" %}` using `extra_attrs=copy_button_extra_attrs`, keeping the `content_copy` icon and the `data-copy-label` span inside
- [x] 2.3 Verify the rendered `data-copy-url="..."` attribute is unchanged so existing tests still pass

> Note: the design proposed an `attrs` dict, but the Unfold button component renders `attrs` **twice** (verified empirically). `extra_attrs` with a `mark_safe` string renders once and correctly, so it was used instead.

## 3. Migrate blog image copy-link to the copy-button pattern

- [x] 3.1 Remove `copy_link` from `BlogImageAdmin.actions_row` and delete the `copy_link` method + the cookie logic in `blog/admin.py`
- [x] 3.2 Remove the now-unused `messages`, `redirect`, and `unfold.decorators.action` imports; keep `get_media_url` (used by the new `change_view`)
- [x] 3.3 Add `BlogImageAdmin.change_view` injecting `copy_button_extra_attrs` (absolute media URL via `get_media_url`, only when `obj.image` exists)
- [x] 3.4 Create `project/templates/admin/blog/blogimage/change_form.html` overriding `object-tools-items` to render the copy button via the Unfold component when `copy_button_extra_attrs` is present, then `{{ block.super }}`
- [x] 3.5 Keep `Media.js = ["js/copy_clipboard.js"]` on `BlogImageAdmin`

## 4. Update docs

- [x] 4.1 `docs/stripe-subscriptions.md` — rewrite Admin controls: state-based visibility matrix, copy button with preloaded URL, remove the `copy_to_clipboard` cookie sentence and the "POST-only" claim
- [x] 4.2 `docs/testing-stripe.md` — L68: operator clicks the "Copiar link" button
- [x] 4.3 `docs/django-image-copy-link.md` — rewrite to the client-side copy-button pattern; remove cookie/auto-copy content
- [x] 4.4 `docs/django-project-setup.md` — update the `copy_clipboard.js` snippet to the current click-to-copy implementation; remove the `add_tailwind_styles.js` reference
- [x] 4.5 `docs/django-unfold-admin.md` — remove the `add_tailwind_styles.js` section and its script reference; update the clipboard cross-reference; add a "changeform actions + copy-link button" pattern note (section 7.3)

## 5. Tests & verification

- [x] 5.1 Add `test_blog_image_change_form_shows_copy_button` and `test_blog_image_change_form_hides_copy_button_without_file` to `blog/tests.py`
- [x] 5.2 Run `python manage.py check` — no issues
- [x] 5.3 Run `python manage.py test subscriptions blog artworks` — 223 tests pass
- [x] 5.4 Run `python manage.py collectstatic --dry-run` — no errors, no missing `add_tailwind_styles.js` reference
- [x] 5.5 Grep the repo for leftover `add_tailwind_styles` / `copy_to_clipboard` references in active code/templates/docs — none remain in scope