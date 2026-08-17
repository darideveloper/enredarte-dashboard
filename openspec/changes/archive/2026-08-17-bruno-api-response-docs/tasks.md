## 1. Prepare response-shape references

- [x] 1.1 Read `artworks/serializers.py`, `project/pagination.py`, and `project/handlers.py` to extract the exact per-resource list-item and detail JSON shapes (field names, `RefSerializer {id, slug}` refs, translation dicts, absolute media URLs, price number types).
- [x] 1.2 Define the shared `docs` block template (purpose, auth note, `## Status codes`, `## Response (200)`, `## Error (401)` / `## Error (404)`) and one abbreviated JSON example per resource shape.

## 2. Taxonomy resources (identical base shape + `translations: {lang: {name}}`)

- [x] 2.1 Add `docs` block to `Disciplines/GET list.bru` and `Disciplines/GET detail.bru` (detail documents the `404` error envelope).
- [x] 2.2 Add `docs` block to `Techniques/GET list.bru` and `Techniques/GET detail.bru`.
- [x] 2.3 Add `docs` block to `Themes/GET list.bru` and `Themes/GET detail.bru`.
- [x] 2.4 Add `docs` block to `Formats/GET list.bru` and `Formats/GET detail.bru`.
- [x] 2.5 Add `docs` block to `Scales/GET list.bru` and `Scales/GET detail.bru`.

## 3. People and place resources

- [x] 3.1 Add `docs` block to `Artists/GET list.bru` and `Artists/GET detail.bru` (fields include `name`, `email`, `website`, `photo`, `birth_year`, `death_year`, `location`, `social_links`, `translations: {lang: {bio}}`).
- [x] 3.2 Add `docs` block to `ArtCurators/GET list.bru` and `ArtCurators/GET detail.bru` (fields include `name`, `email`, `website`, `photo`, `translations: {lang: {bio}}`).
- [x] 3.3 Add `docs` block to `Locations/GET list.bru` and `Locations/GET detail.bru` (`translations: {lang: {name}}`).

## 4. Gallery resource

- [x] 4.1 Add `docs` block to `Galleries/GET list.bru` and `Galleries/GET detail.bru` (fields include `logo`, `curator` ref, `translations: {lang: {name, description}}`, `artwork_links`).

## 5. Artwork resource

- [x] 5.1 Add `docs` block to `Artworks/GET list.bru` (documents `artist` ref, taxonomy arrays of `{id, slug}`, `price_mxn`/`price_usd` as numbers, `translations: {lang: {title, description}}`, `images`, `gallery_links`).
- [x] 5.2 Add `docs` block to `Artworks/GET detail.bru` (same shape as list item, plus `404` error envelope).

## 6. Document the convention for future endpoints

- [x] 6.1 Add a subsection to `docs/django-bruno.md` §6 documenting the mandatory `docs` block convention (purpose, auth, status codes, expected-response JSON example) and pointing at the `bruno-request-docs` spec.

## 7. Verification

- [x] 7.1 Confirm all 20 `.bru` files parse: each contains exactly one `docs` block placed after the `headers` block, with valid Bruno syntax.
- [x] 7.2 Confirm every `docs` block lists the `200` (and `401`) status code, every detail block lists `404`, and every error code shows the `{status, message, data}` envelope.
- [x] 7.3 Confirm the JSON examples match `artworks/serializers.py` field shapes and `project/pagination.py` envelope (no invented fields, prices as numbers, absolute media URLs).
- [x] 7.4 Confirm no Python/runtime files changed and `git diff` only touches the 20 `.bru` files and `docs/django-bruno.md`.