# Secure Catalog API — Design

## Context

The catalogue endpoint `GET /api/catalog/` is the single public route in the project: `CatalogAPIView` (artworks/views.py:12) overrides the global `IsAuthenticated` with `permission_classes = [AllowAny]`, so DRF still *runs* the global dual authentication scheme (Token then Session) but never *enforces* it. The archived change `2026-08-11-add-public-catalog-api` deliberately kept it public (decision D4: "no build token — the data is inherently public").

That decision is now inverted: the data is treated as sensitive, and the SSG build (separate Astro repo) can authenticate. Requirements (delta spec) now say the endpoint must be authenticated while keeping the dual `TokenAuthentication` + `SessionAuthentication` and the unpaginated, single-fetch payload.

Because DRF keeps authentication classes global and applies them to every view, the only real change on the backend is the permission gate: drop `AllowAny`, let the global `IsAuthenticated` take over. No new auth scheme is introduced — the existing `rest_framework.authtoken` Token already **is** an API key (`Authorization: Token <key>`).

```
          BEFORE                               AFTER
   ┌───────────────┐                    ┌───────────────┐
   │ AllowAny      │                    │ IsAuthenticated│
   │ auth runs but │                    │ Token + Session│
   │ never gates   │                    │ gates request  │
   └───────────────┘                    └───────────────┘
        ▲ 200 anonymous                       ▲ 401 anonymous
        ▲ 200 token                           ▲ 200 token
        ▲ 200 session                         ▲ 200 session
```

## Goals / Non-Goals

**Goals:**
- Close the only public gate: anonymous requests to `/api/catalog/` return `401`.
- Use the existing DRF Token as the build API key; keep the dual auth exactly as configured.
- Provide a documented way to provision a dedicated build credential (machine user + token) via the Django admin.
- Keep the catalog payload shape, buyable-only scoping, and no-pagination behaviour byte-for-byte identical.
- Update tests, Bruno collection, and `docs/django-drf.md` so the new contract is the single source of truth.

**Non-Goals:**
- No new authentication scheme (no `X-API-Key` header, no JWT, no custom auth class).
- No per-capability authorization model (role-based access to the catalog). Why: the only consumer is the SSG build; distribute one token, revoke by deleting it. YAGNI.
- No rate limiting, IP allow-listing, or auditing beyond Django's existing admin History for the machine user.
- No schema/data migration: sign up and Token rows are plain core auth models, created via the Django admin.
- No frontend repo changes here — only the API contract the Astro repo must honour.

## Decisions

### D1 — The API key IS the DRF Token
The SSG build authenticates with `Authorization: Token <key>`, exactly like any other API client (docs/django-drf.md section 6). No header inventing, no key model, no new parsing code.

- **Alternative considered:** custom `X-API-Key` via a new authentication class.
  Rejected: adds a parallel key mechanism when a first-class one already exists, ships auth-class code and docs for zero benefit. It also contradicts the user's explicit stance of keeping the default dual auth on both views — reusing Token keeps "both views, dual auth" literally true.

### D2 — Drop `AllowAny`; rely on the global `IsAuthenticated`
`CatalogAPIView.permission_classes` changes from `[AllowAny]` to no override (inherits the settings default). `pagination_class = None` stays.

- **Why a machine user and not any user?** `IsAuthenticated` accepts *any* authenticated user's token. The dedicated machine user (`catalog-ssg`) makes ownership and revocation explicit: provisioning one key per consumer, deleting it kills that build credential without touching staff accounts.
- **Security parity:** any authenticated user can already see prices/works via Django Admin; `IsAuthenticated` matches the exposure the data had within the admin, so this is not a widening.

### D3 — Provision via the Django admin
The build credential is a plain DRF `Token` owned by a dedicated machine user. Both are created interactively in Django admin — the user via the registered `UserAdmin` (project/admin.py:16) and the token via the registered `TokenAdmin` (project/admin.py:31) — following the existing admin workflow. No custom command is added to the codebase.

1. In Django admin, create user `catalog-ssg` (or a chosen username) with an unusable password, non-staff, non-superuser.
2. Under the "Auth tokens" admin section, add a token for that user and copy the generated key once.
3. The key is pasted into the SSG build environment as `CATALOG_API_TOKEN` (never committed).

- **Alternative considered:** seed via fixture. Rejected: fixtures would bake a shared token into the repo — the exact anti-pattern the original change called out.
- **Alternative considered:** data migration. Rejected: migrations shouldn't mint credentials at apply time (unrollable secret churn).

### D4 — Tests encode the new contract
Replace `test_public_and_unpaginated` (artworks/tests.py:1608) semantics:
- Anonymous `GET /api/catalog/` → `401`.
- `TokenAuthentication` with a valid token → `200` + full payload.
- `SessionAuthentication` (login via test client) → `200`.
- Keep every existing scoping/shape test unchanged (buyable only, keys, bilingual, images). Tests create their own user+token with `APIClient().credentials(HTTP_AUTHORIZATION="Token ...")`, not the admin-provisioned credential.

### D5 — Frontend contract (Astro repo, tracked here as spec)
On every build the SSG must send the documented header, reading the key from the build environment:
```
Authorization: Token ${CATALOG_API_TOKEN}
```
The token value comes from the key generated when provisioning the machine user in Django admin (D3). The build SHALL fail hard (non-zero exit) on `401` rather than emit a silently-empty site (matches the existing "one fetch, wholesale-replaceable payload" model).

## Risks / Trade-offs

- **Breaks builds until Astro sends the token** → Mitigation: `401` is loud; the frontend fails the build. Deploy order (backend first, or token present before merge) is documented in the migration plan. The old Astro release in production keeps its previously built pages until its next build — and that next build must already carry the token.
- **Token leakage in build envs / repo** → Mitigation: the key is generated once in Django admin and never committed; Bruno environment files (e.g. `dev.bru`) are gitignored and only the `dev.bru.example` template with a `<paste-token-here>` placeholder is committed; docs flag it as a secret. Revocation = deleting the token in Django admin (or `Token.objects.get(user__username="catalog-ssg").delete()`).
- **A leak of any user token exposes the catalog** → inherent to `IsAuthenticated`; the catalog is no more sensitive than the admin a logged-in user already sees. If catalogue confidentiality ever exceeds admin access, revisit with a custom permission scoped to the machine user (deferred, YAGNI).
- **Shape coupling to the frontend persists** → unchanged from the archived design: contract asserted by tests; `/api/catalog/v2/` convention if the shape must ever break.

## Migration Plan

1. Ship backend change (merge these tasks): permission change, updated tests, docs, Bruno.
2. In the environment running the SSG build, create the machine user and its token in Django admin (D3) and paste the generated key into the build env as `CATALOG_API_TOKEN` (never in git).
3. Update the Astro repo to send the header (or deploy both together so no build runs without the token).
4. Deploy backend after (or with) the Astro change.

**Rollback:** revert the permission line + tests to allow anonymous; payload and scoping need no revert. Existing built pages stay valid.

## Open Questions

- Username naming convention for the machine user: `catalog-ssg` proposed; any username chosen when creating it in Django admin works.
- Does the SSG build currently run anywhere we should pre-provision the token during this change, or is it purely the frontend repo's concern for now?