# Design: add-sales-bruno-docs

## Context

The Bruno workspace (`bruno/`, Bruno 3.0+, `workspace.yml` + one
collection) holds 22 authenticated `GET list/detail` requests (seq 1–22)
with mandatory `docs` blocks (`bruno-request-docs` spec, guide in
`docs/django-bruno.md` §6.4). The sales endpoints from
`add-artwork-stripe-sales` are the first **public** (`AllowAny`) and first
**write** (`POST`) endpoints in the collection: no `Authorization` header,
JSON bodies required, slugs are uuid-hex order tokens (unguessable, so no
real slug can be committed), and `POST buy` returns only `{checkout_url}`
— the order slug needed by the next two requests only surfaces in the
Stripe success redirect. Stakeholders: frontend devs (runnable flow +
docs) and operators (smoke test).

## Goals / Non-Goals

**Goals:**
- Three runnable, documented sales requests a frontend dev can execute
  top-to-bottom against dev.
- `docs` blocks faithful to the serializers (no invented fields).
- A headless `bru run Sales/` smoke test that needs no credentials.

**Non-Goals:**
- No collection restructuring (existing folders untouched).
- No `docs/django-bruno.md` rewrite — one short public-endpoint note only
  (§6.1/§6.4: sales under `/api/artworks/` are `AllowAny`, no
  `Authorization` header, document throttles instead of Token).
- No CI wiring (smoke test is documented + manually runnable; CI hook is
  a separate change).
- No authenticated sales variants (none exist).

## Decisions

### D1. One `Sales/` flow folder, not URL-mirrored placement
- `Sales/` holds buy → summary → delivery in run order (seq 23–25).
- **Why:** the consumer goal is "run the purchase flow", not "browse
  resources"; buy is an artwork action and orders are a separate path, so
  URL-mirroring would split the flow across two folders.
- Alternative rejected: `POST buy.bru` under `Artworks/` + `Orders/`
  folder — more literal to the existing per-resource convention, but
  hostile to the handoff use case (operator-confirmed: `Sales/`).

### D2. Example artwork slug for buy, fake-hex literals for orders + explicit handoff note
- `POST buy.bru` uses an example artwork slug (`obra-ejemplo` — artwork
  slugs are human-readable); order URLs carry an obviously-fake hex slug
  (e.g. `0123456789ab`); each `docs` block instructs: run buy → pay (or
  copy `?order=` from the success redirect) → paste the real order slug
  into the next requests.
- **Why operator-confirmed:** placeholder style decision (fake-hex).
- Alternative rejected: Bruno path params — prettier URLs, but still
  manual (nothing to chain *from*, since buy returns no slug), so it
  adds syntax without removing any step.

### D3. `docs` blocks carry the full status matrix, including backend-only codes
- Buy docs list 201/200/400/404/409/502/503/429 with the project error
  envelope; summary docs explain 200-vs-404 visibility + polling recipe
  (3s, ~60s cap, from `docs/artwork-sales.md`); delivery docs list the
  9+5 fields with max lengths and the 409-as-success rule.
- **Why:** the `docs` tab is the handoff — the frontend dev should never
  need to open Django code for status semantics.

### D4. Smoke test asserts axis, not exact state
- `bru run` asserts buy → `201` **or** `409` (real slug; artwork may already be
  reserved) **or** `404` (committed example slug unknown — benign),
  summary → `200` **or** `404`, delivery skipped-by-design
  (needs a paid order). No credentials, no Stripe calls.
- **Why:** the test must be idempotent and green on any dev DB state;
  exact-state assertions would flake. Delivery stays manual (needs a
  real paid order).

## Risks / Trade-offs

- **[Slugs rot]** Fake-hex slugs never execute successfully — a dev may
  think the API is broken on first click → mitigation: first line of
  each `docs` block says "replace the slug, then Send".
- **[Rate limits in manual testing]** 20 buys/hour is easy to hit while
  poking → mitigation: documented in `docs` + README (wait/retry).
- **[Bru format drift]** Bruno upgrades can change `.bru` syntax →
  mitigation: plain-text diffs, verify by opening the workspace once.
- **[Smoke test is order-blind]** It proves the endpoints respond, not
  that a purchase completes → accepted; full E2E remains task 7.2 of
  the sales change.

## Migration Plan

1. Add the 3 `.bru` files + README section (purely additive, no
   existing file touched except README).
2. Open the workspace in Bruno desktop, run Sales/ top-to-bottom
   against dev, confirm `docs` tabs render.
3. Document the `bru run Sales/` command; no rollback needed (docs-only).

## Open Questions

- None — folder, placeholder style, and smoke-test scope all confirmed
  with the operator (2026-09-17).
