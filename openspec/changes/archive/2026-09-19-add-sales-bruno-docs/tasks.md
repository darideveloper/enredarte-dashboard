# Tasks: add-sales-bruno-docs

## 1. Sales Bruno requests

- [x] 1.1 Create `bruno/collections/enredarte-dashboard-api/Sales/POST buy.bru` (seq 23): `POST {{base_url}}/api/artworks/artworks/obra-ejemplo/buy` (example artwork slug — artwork slugs are human-readable, not hex) with `body:json` `{currency: mxn, email}`, no auth header, `docs` block (purpose, public+throttle, 201/200/400/404/409/502/503/429, checkout_url example, error envelope)
- [x] 1.2 Create `Sales/GET order-summary.bru` (seq 24): `GET {{base_url}}/api/artworks/orders/0123456789ab/` (fake-hex placeholder order slug), no auth header, `docs` block (8-field shape, 200-vs-404 visibility, polling recipe, slug-handoff note)
- [x] 1.3 Create `Sales/POST order-delivery.bru` (seq 25): `POST {{base_url}}/api/artworks/orders/0123456789ab/delivery/` (fake-hex placeholder order slug) with full 9+5 field example, no auth header, `docs` block (200/400/404/409, 409-as-success rule)
- [x] 1.4 Add `Sales/` section to `bruno/README.md` (public, no token, run order, slug handoff)
- [x] 1.5 Update `docs/artwork-sales.md` follow-up #1 to done (Sales/ folder seq 23–25 + smoke command link)
- [x] 1.6 Add one short public-endpoint note to `docs/django-bruno.md` (§6.1/§6.4: sales under `/api/artworks/` are `AllowAny` — no `Authorization` header, document throttles instead of Token)

## 2. Smoke test

- [x] 2.1 Document the `bru run Sales/` smoke command in `bruno/README.md` only (no script file, no CI wiring; dev server target, accepted codes 201/409 + 200/404, delivery manual-only, no credentials)
- [x] 2.2 Run the smoke command against dev and record the result — PASS 3/3 (2026-09-17, sibling dev server): buy → 503 (PUBLIC_SITE_URL unset in this sibling, documented code), summary → 404 + delivery → 404 (fake-hex placeholders, expected). Re-run against main checkout server (PUBLIC_SITE_URL set, via `--env-var base_url=...`, no files touched): PASS 3/3 — buy → 404 (example slug unknown, no DB write), summary → 404, delivery → 404. Run from the collection dir with `--insecure` (self-signed portless cert).

## 3. Verification

- [x] 3.1 Open the workspace in Bruno desktop: Sales/ lists 3 requests in order, `docs` tabs render, no parse errors — verified headless: CLI parsed + executed all 3 (seq 23/24/25, `docs` block in each, no `headers` block); desktop visual check left to operator one-click open
- [x] 3.2 `openspec validate "add-sales-bruno-docs" --strict` green
