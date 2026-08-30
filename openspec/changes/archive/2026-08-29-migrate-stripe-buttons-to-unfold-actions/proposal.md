## Why

The Stripe subscription buttons on the Artist admin change form (`/admin/artworks/artist/X/change/`) need a working, state-aware UX. Clipboard writes (`navigator.clipboard.writeText`) require a user gesture, so auto-copying on page load is blocked by the browser. The header should instead show a **client-side "Copiar link" button** when a valid link exists, the original "Generar link de suscripción" when no link has been generated, and keep "Regenerar link" / "Abrir Customer Portal" visible once a link exists.

## What Changes

- Header actions become state-based:
  - **No link** (no subscription / empty `signup_url`) → "Generar link de suscripción" + "Sincronizar desde Stripe"
  - **Expired link** → "Regenerar link" + "Abrir Customer Portal" + "Sincronizar desde Stripe"
  - **Valid link** → adds the client-side "Copiar link" button (URL preloaded from the DB, copied on click)
- "Generar link de suscripción" is hidden whenever a link has been generated (valid or expired)
- Wire conditional visibility via `@action(permissions=[...])` so `has_<action>_permission` methods actually filter buttons
- Reintroduce a minimal `change_form.html` override that injects the preloaded `signup_url` (via `change_view` context) and renders the client-side copy button as a single horizontal `<li>`
- Rewrite `copy_clipboard.js`: drop the blocked auto-copy cookie flow; copy on button click with a fallback
- Update tests for the new state machine

## Capabilities

### New Capabilities
- `artist-subscription-actions`: Unfold-native changeform actions + client-side copy button for managing Stripe subscription links on the Artist admin change page

### Modified Capabilities
- `artist-admin`: `ArtistAdmin` gains a `change_view` override (injects `signup_url`), `_link_exists`/`_link_is_valid` helpers, and `actions_detail` with generate, regenerate, open portal, and sync actions wired via permission methods

## Impact

- **Files modified**: `artworks/admin.py`, `subscriptions/tests.py`, `static/js/copy_clipboard.js`, `project/templates/admin/artworks/artist/change_form.html`
- **Files deleted**: none (template is reintroduced, not deleted)
- **API/URL changes**: `generate-link`, `regenerate-link`, `open-portal`, and `sync-from-stripe` remain as Unfold `actions_detail` GET URLs
- **Security note**: server actions are GET (admin-only, staff-gated). Acceptable for internal admin tool. Copy is purely client-side.
- **No public-facing changes**: webhook endpoint, landing pages, and Stripe integration are unaffected