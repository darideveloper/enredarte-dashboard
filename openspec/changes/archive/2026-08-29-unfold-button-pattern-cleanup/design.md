## Context

All admin server actions now use Unfold-native patterns: `actions_detail` for the Artist subscription header buttons and `actions_row` for row actions (`edit`). The only buttons that cannot be Unfold *actions* are copy-link buttons — the Clipboard API requires a user gesture on the same page, so a server action (GET → redirect) cannot copy. These are the legitimate exceptions where a custom-injected `<button>` is required.

Two problems exist today:

1. **Blog copy-link is broken.** `BlogImageAdmin.copy_link` (`blog/admin.py:135`) sets a `copy_to_clipboard` cookie and relies on `copy_clipboard.js`. The shared JS was rewritten to click-to-copy on `[data-copy-url]` buttons and no longer reads cookies, so the row action shows "Enlace copiado" but never copies.
2. **Copy buttons hand-roll Tailwind.** Both the Artist copy button (`change_form.html`) and (after migration) the blog copy button duplicate Unfold's button classes instead of using `unfold/components/button.html`.
3. **Dead code.** `static/js/add_tailwind_styles.js` only styles `.btn`, and no template uses `class="btn"` anymore — the file can be deleted.

## Goals / Non-Goals

**Goals:**
- Use Unfold's button component everywhere; custom-inject buttons only where a real client-side `<button>` is required (copy links)
- Restore the blog image "Copiar enlace" feature using the same pattern as the Artist copy button
- Delete the dead `add_tailwind_styles.js`
- Bring every affected doc in line with the current implementation

**Non-Goals:**
- Changing the Artist subscription action set, URL names, or state machine
- Changing `copy_clipboard.js` behavior (already correct)
- Adding new capabilities to the spec catalog
- Touching the public Stripe/webhook flow

## Decisions

### Decision 1: Copy buttons render through Unfold's button component

**Choice**: Both copy buttons use `{% component "unfold/components/button.html" %}` (from `unfold` template library) with `extra_attrs`. The admin injects `copy_button_extra_attrs` — a `mark_safe` string `type="button" data-copy-url="<url>"` — into the change form context; the template renders the component inside the `object-tools-items` `<li>`.

**Why**: This keeps the buttons custom-injected (they must be real `<button>`s with a `data-copy-url` for the JS, and they must carry `type="button"` so they do not submit the surrounding POST form) while eliminating the duplicated hand-rolled Tailwind class string. The component is Unfold's single source of truth for button styling.

**Deviation from `attrs` dict**: The component renders an `attrs` dict **twice** in the opening tag (a Unfold quirk verified empirically: `type="button" data-copy-url="..." type="button" data-copy-url="..."`), producing invalid HTML. `extra_attrs` renders exactly once, so it is used instead; the value is `mark_safe` to avoid auto-escaping the attribute quotes. URLs (Stripe checkout / media) contain no `"`, so double-quoted attribute values are safe.

### Decision 2: Blog copy-link moves from a row action to a change-form copy button

**Choice**: Delete `copy_link` from `BlogImageAdmin.actions_row` and the method itself. Add `BlogImageAdmin.change_view` that injects the absolute media URL (via `get_media_url`) and a `project/templates/admin/blog/blogimage/change_form.html` override that prepends the copy button in `object-tools-items`, mirroring the Artist change form. Keep `Media.js = ["js/copy_clipboard.js"]`.

**Why**: A row action is a navigation link (GET → redirect), which cannot perform a client-side clipboard write. The change-form copy button is the established pattern (Artist). The image already has a `readonly_fields` URL display, so the copy button complements it.

**Trade-off**: Copying now requires opening the image change form instead of a changelist one-click. Acceptable — the image row already has an `edit` action to reach it, and the change form is where the URL is displayed.

### Decision 3: Delete `add_tailwind_styles.js`

**Choice**: Remove the file and its `<script>` include from `project/templates/admin/base.html`.

**Why**: Its only selector is `.btn`, which no template uses. The `.img-preview` entry was already removed (a prior change moved that styling to CSS). Deleting removes a DOMContentLoaded listener and a static asset from every admin page.

### Decision 4: Docs reflect the current implementation

**Choice**: Update the five affected docs to describe: (a) the Artist header actions + copy button and the state-based visibility matrix, (b) the blog image copy button, (c) the new `copy_clipboard.js` click-to-copy behavior, and (d) the removal of `add_tailwind_styles.js`. Remove all references to the `copy_to_clipboard` cookie and "POST-only" admin endpoints.

**Why**: Several docs still document removed behavior (`stripe-subscriptions.md:132-146`, `django-image-copy-link.md`, `django-project-setup.md:596-619`, `django-unfold-admin.md:190-212`), which will mislead future work.

## Risks / Trade-offs

- **[Blog copy UX changes]** → Copying requires the change form; mitigation: the change form is one `edit` click away and already shows the URL.
- **[Component attribute rendering]** → The Artist `change_view` previously injected a raw `signup_url`; switching to the `copy_button_extra_attrs` `extra_attrs` string (documented in Decision 1) requires the template and any tests that assert `data-copy-url="..."` to keep working (the rendered attribute is unchanged).
- **[Docs drift risk]** → Mitigated by updating all five docs in the same change; no remaining `copy_to_clipboard` cookie references in active docs.