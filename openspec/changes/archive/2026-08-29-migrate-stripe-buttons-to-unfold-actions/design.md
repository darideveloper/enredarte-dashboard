## Context

The Artist admin change form has 4 Stripe subscription buttons rendered via Unfold `actions_detail` (generate, regenerate, portal, sync). Clipboard auto-copy on page load was blocked by the browser (`Clipboard write was blocked due to lack of user activation`) because `navigator.clipboard.writeText()` requires a user gesture. The flow needed a client-side copy button the admin clicks, while keeping the four server actions visible according to subscription state.

Unfold renders `actions_detail` items as links in a horizontal `<ul>` in the header. Conditional visibility is only enforced when `@action(permissions=[...])` is passed — without it, `has_<action>_permission` methods are never consulted and buttons always show.

## Goals / Non-Goals

**Goals:**
- Show "Copiar link" (client-side) when a valid link exists; "Generar link de suscripción" when no link has been generated
- Keep "Regenerar link" and "Abrir Customer Portal" visible whenever a link exists (valid or expired)
- Keep "Sincronizar desde Stripe" always visible
- Fix button visibility wiring so permission methods actually filter
- Avoid the previous vertical-stacking overflow in the header

**Non-Goals:**
- Changing the Stripe integration logic or the `generate_link`/`sync_from_stripe` behaviors
- Modifying webhook handling or landing pages
- Changing the subscription model or state derivation
- Adding new subscription actions

## Decisions

### Decision 1: State machine — link generated vs no link

**Choice**: Two helpers drive the header:
- `_link_exists(sub)` — subscription has a `signup_url` (valid or expired)
- `_link_is_valid(sub)` — exists AND non-expired (`signup_url_expires_at` in the future, or unset)

Permission/visibility matrix:
- **No link** (no subscription or empty `signup_url`): "Generar link de suscripción" + "Sincronizar desde Stripe"
- **Expired link**: "Regenerar link" + "Abrir Customer Portal" + "Sincronizar desde Stripe"
- **Valid link**: adds the client-side "Copiar link" button on top of the expired set

**Why**: The user wants all buttons except "Generar link" whenever a link has already been generated. "Regenerar link" is the tool for expired links (creates a fresh session), so "Generar link" is only for artists that have never had one.

### Decision 2: Copy must be client-side (no server round-trip)

**Choice**: The copy button reads the preloaded `signup_url` from the DOM and copies on click, entirely client-side.

**Alternative considered**: An `actions_detail` server action — rejected because server actions navigate (GET → redirect), and clipboard writes require a user gesture on the same page.

**Why**: `change_view` injects `signup_url` into context; the template renders `<button data-copy-url="{{ signup_url }}">`; `copy_clipboard.js` attaches a click handler. The click provides the user activation the clipboard API needs.

### Decision 3: Minimal template override (single horizontal `<li>`)

**Choice**: Reintroduce `project/templates/admin/artworks/artist/change_form.html` overriding `object-tools-items` to prepend the copy button as a single `<li>` styled with Unfold's button classes, then `{{ block.super }}`.

**Why**: The `object-tools-items` block renders inside Unfold's horizontal flex `<ul>` (`tab_actions.html`). A single `<li>` aligns with the history/sync buttons — no `flex-col` container, so no vertical stacking/overflow. This is the only way to get a client-side button (not a navigation link) into the header row.

### Decision 4: Wire permission methods via `@action(permissions=[...])`

**Choice**: Pass `permissions=["generate_link"]`, `permissions=["regenerate_link"]`, `permissions=["open_portal"]`, and `permissions=["sync_from_stripe"]` to the respective `@action` decorators.

**Why**: Unfold's `_filter_unfold_actions_by_permissions` skips filtering when `allowed_permissions` is unset. Adding `permissions` makes the `has_<action>_permission` methods actually control button visibility (this was silently broken before).

### Decision 5: Drop the cookie clipboard flow

**Choice**: Remove `_set_clipboard_cookie` and the `copy_to_clipboard` cookie mechanism. `copy_clipboard.js` no longer reads a cookie on load.

**Why**: The cookie existed to pass the freshly generated URL to the next page for auto-copy. Now the URL lives in the DB and is injected into the DOM by `change_view`, so the cookie is dead weight. The success message becomes "Link de suscripción generado." (it no longer claims the link was copied).

### Decision 6: Keep `regenerate_link` and `open_portal` (restored)

**Choice**: Both actions remain in `actions_detail`, gated by permission methods (`has_regenerate_link_permission`, `has_open_portal_permission` → `_link_exists`). They were briefly removed, then restored per user request ("all buttons except Generar when a link is generated").

**Why**: Regenerate handles expired links (fresh checkout session); open portal gives the artist their billing dashboard. Both are only shown once a link exists. `@action(permissions=[...])` keeps visibility enforced.

## Risks / Trade-offs

- **[No CSRF on server actions]** → Mitigated by admin-only access (staff-gated). Acceptable for internal tools.
- **[Active paid artist shows "Generar link"]** → Webhook clears `signup_url` on checkout completion, so an active subscriber has no valid link and the generate button shows. Matches the requested "no link → generate" rule; harmless (`get_or_create` + fresh session).
- **[Copy depends on secure context]** → `copy_clipboard.js` falls back to `execCommand('copy')` via a temp textarea, then `prompt()` for manual copy if that fails.
- **[Button ordering]** → Unfold renders `actions_detail` items in list order; the copy button renders before history/sync (leftmost) via the template override, as chosen.