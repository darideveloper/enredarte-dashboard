# Secure Catalog API — Tasks

## 1. Backend permission change

- [x] 1.1 Remove `AllowAny` from `CatalogAPIView` (artworks/views.py) so it inherits the global `IsAuthenticated`; keep `pagination_class = None`.

## 2. Tests

- [x] 2.1 Replace `test_public_and_unpaginated` (artworks/tests.py:1608) with an anonymous-request test asserting `401`.
- [x] 2.2 Add a Token-auth test: `APIClient().credentials(HTTP_AUTHORIZATION="Token <key>")` returns `200` with the full payload.
- [x] 2.3 Add a Session-auth test: logged-in test client returns `200`.
- [x] 2.4 Run the full test suite and confirm all existing scoping/shape tests (buyable-only, bilingual keys, images) still pass unchanged.

## 3. Tooling & docs

- [x] 3.1 Update the Bruno collection: `Public Catalog/GET catalog.bru` moves under an authenticated folder and sends `Authorization: Token {{token}}`.
- [x] 3.2 Extend `docs/django-drf.md` (section 6): document the machine user, token creation in Django admin (`TokenAdmin`), the SSG header contract `Authorization: Token ${CATALOG_API_TOKEN}`, and revocation steps.

## 4. Frontend contract handoff

- [x] 4.1 Confirm the Astro repo change is tracked (header from build env, hard-fail on `401`) — backend contract already fixed by tasks 1–3.
