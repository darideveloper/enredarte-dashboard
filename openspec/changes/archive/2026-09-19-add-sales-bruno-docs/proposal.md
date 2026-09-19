# Proposal: add-sales-bruno-docs

## Why

The artwork sales flow (`add-artwork-stripe-sales`) shipped three public API
endpoints with zero Bruno coverage, so frontend developers and operators
have no runnable, documented requests to exercise the purchase flow. The
`bruno-request-docs` spec already mandates a `docs` block for every future
endpoint — this change fulfills that mandate for sales and adds the first
headless smoke test (possible because sales endpoints need no token).

## What Changes

- New `Sales/` flow folder in `bruno/collections/enredarte-dashboard-api/`
  with three requests in run order (seq 23–25):
  - `POST buy.bru` — `POST {{base_url}}/api/artworks/artworks/:slug/buy/`
    (example artwork slug `obra-ejemplo`) with JSON body `{currency, email}`; docs cover 201/200/400/404/409/
    502/503/429 plus the error envelope.
  - `GET order-summary.bru` — `GET {{base_url}}/api/artworks/orders/:slug/`
    with a fake-hex placeholder slug; docs carry the 8-field summary shape,
    the 404/polling contract, and the slug-handoff note (buy returns only
    `checkout_url`; the slug comes from the Stripe success redirect, so
    auto-chaining between requests is impossible).
  - `POST order-delivery.bru` — `POST {{base_url}}/api/artworks/orders/:slug/delivery/`
    with the full 9-required + 5-optional field example; docs cover 200/
    400/404/409.
  - Public-endpoint convention: no `Authorization` header; `docs` blocks state
  "public, throttled" (`artwork_buys 20/hour`, `artwork_orders 60/hour`)
  instead of the Token requirement. Only `{{base_url}}` is referenced —
  no hardcoded hosts; buy uses the example artwork slug `obra-ejemplo`,
  order requests use obviously-fake hex literals.
- `bruno/README.md` gains a `Sales/` section (public, no token needed).
- `docs/artwork-sales.md` follow-up #1 flipped to done (Sales/ folder +
  smoke command link).
- `docs/django-bruno.md` gains one short public-endpoint note (§6.1/§6.4:
  sales are `AllowAny`, document throttles instead of Token).
- Headless smoke test: `bru run` over `Sales/` against the dev server
  (buy → expect 201/409, or 404 with the example slug; summary → expect 200/404), runnable without
  credentials.

## Capabilities

### New Capabilities

- `sales-bruno-smoke`: Headless `bru run` smoke coverage for the public
  sales flow — what it runs, against which environment, and the accepted
  status codes per request.

### Modified Capabilities

- `bruno-api-collection`: The collection gains a `Sales/` flow folder
  (buy, order-summary, order-delivery, seq 23–25) alongside the existing
  per-model folders; sales requests use `{{base_url}}` only and carry no
  auth header.

## Impact

- **Files**: 3 new `.bru` files, `bruno/README.md` (one section),
  `docs/artwork-sales.md` (follow-up #1 flipped to done),
  `docs/django-bruno.md` (one short public-endpoint note),
  smoke command documented in README only (no script file, no CI wiring).
- **No runtime code, no API changes, no new dependencies** (per the
  `bruno-api-collection` no-runtime-dependency requirement).
- **Docs**: `docs` blocks derived from `artworks/serializers.py`,
  `artworks/views.py`, and `docs/artwork-sales.md`; no invented fields.
