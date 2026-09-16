## Context

The artworks API (10 DRF `ModelViewSet`s on a `DefaultRouter` in `artworks/urls.py`) is mounted at `apis/artworks/` from `project/urls.py:14` — the only mount in the project using the plural `apis/` prefix. The blog API mounts at `api/blog/`, and all project documentation (`docs/enredarte-artworks-blog-api.md`, `docs/django-drf.md`, `docs/enredarte-overview.md`, Stripe docs) already describes `/api/artworks/` as canonical. The only external consumer is the separate Astro landing repo (`enredarte.mx`), which builds against these endpoints at build time with a DRF Token.

No Python code resolves artworks URLs via `reverse()` — every `reverse()` in the repo targets `admin:*`, `blog-posts-*`, or `subscriptions:*` — so the prefix exists in exactly one runtime line plus hardcoded strings in tests, Bruno files, and specs.

## Goals / Non-Goals

**Goals:**
- Serve all 21 artworks endpoints (router root + 10 list + 10 detail) under `/api/artworks/`.
- Update every in-repo consumer (tests, Bruno collection + README, active specs) so the repo is self-consistent and `manage.py test` passes.
- Keep the change mechanical and reviewable: no serializer, queryset, auth, or pagination behavior changes.

**Non-Goals:**
- No backwards-compatibility shim: no dual mount, no `apis/ → api/` redirect (direct cutover).
- No rewrite of archived change docs (`openspec/changes/archive/**` is history).
- No `docs/` changes (already describe `/api/`).
- No changes to the landing repo itself (separate repository; coordination only).

## Decisions

- **Clean cut over dual-mount/redirect.** The API is GET-only with a single build-time consumer, and the old prefix is a typo, not a versioned contract. A shim would outlive its welcome and redirect + `Authorization` header forwarding is fragile across HTTP clients (some strip auth on 301). Alternative considered: mount both prefixes for one deploy cycle — rejected as unnecessary machinery for a one-line fix with one known consumer.
- **Change only the mount point, not the router.** The `apis` string appears only in `project/urls.py:14`; `artworks/urls.py` registers bare resource names. One-line runtime diff keeps blast radius minimal and all 21 URLs move atomically.
- **Scoped string replacement for consumers.** Replace `apis/artworks/` → `api/artworks/` (and `{{base_url}}/apis/` → `{{base_url}}/api/`) only in the inventoried files (`artworks/tests.py`, 20× `.bru`, `bruno/README.md`, 4 active specs). No repo-wide sed — archive history must keep the old strings.
- **Spec deltas mirror the code move.** Each modified capability gets a delta spec with full updated requirement blocks; the base specs are updated at archive time.

## Risks / Trade-offs

- [Risk] A live caller (landing build, script, partner) still hits `/apis/*` and gets 404 after deploy → Mitigation: confirm with the landing repo owner before deploy; deploy backend first, then trigger a landing rebuild against the new prefix.
- [Risk] In-progress changes `add-artwork-stripe-sales` (proposal, design, `artwork-sales` spec, `artworks-rest-api` delta) and `-artwork-mockups` (design, `artworks-rest-api` delta) reference the old prefix and will conflict at merge time → Mitigation: rebase both changes after this lands (noted in tasks).
- [Risk] Over-broad replacement corrupts archive docs or unrelated strings → Mitigation: file-scoped edits only; verify with `rg "apis/"` that remaining hits are archive-only.
- [Trade-off] Old URLs die loudly (404) instead of politely (redirect) → Accepted: surfaces stale callers immediately; error envelope (`{status, message, data}`) still applies to 404s per the existing spec.

## Migration Plan

1. Land this change (backend): mount moves to `api/artworks/`; tests + Bruno + specs updated in the same commit.
2. Notify landing repo owner; update its build config to `/api/artworks/*` and rebuild.
3. Verify: `GET /api/artworks/artists/` → 200 with token; `GET /apis/artworks/artists/` → 404.
4. Rollback (if needed): revert the single mount line plus consumer strings — one commit revert, no data migration involved.

## Open Questions

- Is any production caller besides the landing build hitting `/apis/*` today? (Assumed no; confirm before deploy.)
- Who owns the landing-repo URL update, and is a coordinated rebuild scheduled?
