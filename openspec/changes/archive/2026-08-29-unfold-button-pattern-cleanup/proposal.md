## Why

The admin should use Unfold's native button patterns everywhere possible, keeping custom-injected buttons **only** for client-side copy links (the clipboard API requires a user gesture on the same page, which a server-side Unfold action cannot provide). Currently there are two inconsistencies: the blog's image `copy_link` row action still uses the removed cookie mechanism (so it no longer actually copies), and the copy-link buttons hand-roll Tailwind class strings instead of using Unfold's button component. Additionally, `static/js/add_tailwind_styles.js` is dead code — its `.btn` selector has no consumers left.

## What Changes

- **Migrate blog image copy-link to the client-side copy-button pattern**: remove the cookie-based `copy_link` row action from `BlogImageAdmin`; add a `change_view` that injects the absolute image URL and a `blog/blogimage/change_form.html` override that renders a "Copiar enlace" button (`data-copy-url`), matching the Artist change form
- **Use Unfold's button component for copy buttons**: the Artist and blog copy buttons keep being custom-injected (a real `<button>`, not a navigation link) but render via `{% component "unfold/components/button.html" %}` with an `attrs` dict instead of hand-rolled Tailwind classes
- **Remove dead `add_tailwind_styles.js`** and its `<script>` include in `project/templates/admin/base.html`
- **Update all docs** that reference the old cookie/auto-copy mechanism, the removed `add_tailwind_styles.js`, and the admin-controls/button set (`stripe-subscriptions.md`, `testing-stripe.md`, `django-image-copy-link.md`, `django-project-setup.md`, `django-unfold-admin.md`)

## Capabilities

### New Capabilities

None — this is a cleanup + a behavior change to an existing capability.

### Modified Capabilities
- `blog-admin`: the `BlogImage` copy-link requirement changes from a cookie-setting row action to a client-side copy button on the image change form

## Impact

- **Files deleted**: `static/js/add_tailwind_styles.js`
- **Files modified**: `project/templates/admin/base.html`, `artworks/admin.py`, `blog/admin.py`, `docs/stripe-subscriptions.md`, `docs/testing-stripe.md`, `docs/django-image-copy-link.md`, `docs/django-project-setup.md`, `docs/django-unfold-admin.md`
- **Files created**: `project/templates/admin/blog/blogimage/change_form.html`
- **No API/URL changes**: the Artist `actions_detail` URLs and blog admin row actions for `edit` are unchanged; the blog `copy_link` row action is removed (internal admin only)
- **Functional fix**: restores the blog image "Copiar enlace" feature that the shared `copy_clipboard.js` rewrite had silently broken
- **No public-facing changes**: webhook, landing pages, and Stripe integration are unaffected