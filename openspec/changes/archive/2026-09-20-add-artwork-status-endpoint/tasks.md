## 1. Backend endpoint

- [x] 1.1 Add `artwork_status` detail action (`GET`, `url_path="status"`, `AllowAny`, `authentication_classes=[]`, `ScopedRateThrottle`) to `ArtworkViewSet` in `artworks/views.py`, returning `{slug, status, status_display, price_mxn, price_usd, updated_at}` via a single-row `.only(...)` fetch filtered on `slug/is_active/artist__is_active`, `404` with `{status: error, message: Not found., data: {}}` when missing/inactive, and `Cache-Control: no-store` on 200
- [x] 1.2 Add `elif action == "artwork_status"` → `throttle_scope = "artwork_status"` branch in `ArtworkViewSet.get_throttles()`
- [x] 1.3 Add `"artwork_status": "120/hour"` to `DEFAULT_THROTTLE_RATES` in `project/settings.py`

## 2. Backend tests

- [x] 2.1 Add `StatusArtworkApiTestCase` in `artworks/tests.py` mirroring `VisitArtworkApiTestCase`: 200 shape/keys/types for available + sold + reserved, 404 unknown slug, 404 inactive artwork, 404 inactive artist, no-token public access, `no-store` header present, no DB write on GET
- [x] 2.2 Add throttle wiring tests: `status` action uses `ScopedRateThrottle` with scope `artwork_status`, rate `120/hour` present in settings, and 429 on exceeded rate (mutate `REST_FRAMEWORK` rates in place + `cache.clear()`, per existing throttle tests)
- [x] 2.3 Run `venv/bin/python manage.py test artworks --verbosity=2` green

## 3. Bruno API file

- [x] 3.1 Create `bruno/collections/enredarte-dashboard-api/Artworks/GET status.bru` (meta `name: GET status`, `seq: 27`; `get { url: {{base_url}}/api/artworks/artworks/ciudad-reflejada/status/, body: none, auth: none }`; no `Authorization` header; `docs` block with title, public+throttled note (`artwork_status 120/hour`), status codes 200/404/429, 200 + error JSON, slug-swap guidance)
- [x] 3.2 Smoke-test the `.bru` request against local dev server (200 on a seed slug, 404 on unknown slug) and confirm edge `Cache-Control: no-store` header
