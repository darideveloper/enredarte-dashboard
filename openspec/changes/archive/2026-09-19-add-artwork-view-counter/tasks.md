## 1. Throttle scope

- [x] 1.1 Add `"artwork_views": "20/hour"` to `DEFAULT_THROTTLE_RATES` in `project/settings.py`.

## 2. Visit endpoint

- [x] 2.1 Add public `visit` detail `@action` (`POST`, `url_path="visit"`, `AllowAny`, empty `authentication_classes`, `ScopedRateThrottle`) on `ArtworkViewSet` in `artworks/views.py` that `F()`-increments `views_count` for the active slug and returns `{"views_count": N}` (`404` for unknown/inactive).
- [x] 2.2 Branch `get_throttles()` on `action == "visit"` to set `throttle_scope = "artwork_views"`.

## 3. Tests

- [x] 3.1 Anonymous `POST visit` increments `0 -> 1` and returns `{"views_count": 1}`.
- [x] 3.2 Second `POST` increments again (raw, no dedup); unknown slug and inactive artwork return `404` with no increment.
- [x] 3.3 `visit` enforces the `artwork_views` throttle scope (`429` test with in-place `1/min` rate); catalog `GET artworks/` still `401` for anonymous callers.
- [x] 3.4 Run `venv/bin/python manage.py test artworks --verbosity=2`.

## 4. Manual verify

- [x] 4.1 Bruno `POST /api/artworks/artworks/<slug>/visit/` returns count+1; artist "Más visitadas" block reorders accordingly.

## 5. Bruno docs

- [x] 5.1 Add `Artworks/POST visit.bru` (seq 26, real seed slug, `body: none`, no `headers` block, `docs` block per `bruno-request-docs`).
- [x] 5.2 Note the public-counter exception in `bruno/README.md` and `docs/django-bruno.md`.
- [x] 5.3 Verify: `bru run` the file headless (PASS), live curl of the exact URL (`1` → `2`), no secrets committed (`dev.bru` stays gitignored).
