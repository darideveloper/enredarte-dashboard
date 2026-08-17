## Why

`GET /api/catalog/` is the only route that bypasses the project's default auth: it overrides the global `IsAuthenticated` with `AllowAny`. To keep both API views on the default dual auth (Token + Session), the catalog must stop serving anonymous requests — and since the Astro SSG build fetches the catalogue, it will authenticate with an API key instead of a public call. No new auth scheme is introduced.

## What Changes

- **BREAKING** `GET /api/catalog/` no longer accepts anonymous requests; it SHALL require authentication, defaulting to the global `IsAuthenticated` permission.
- The existing DRF `Token` (authtoken) becomes the API key for the SSG build: the frontend sends `Authorization: Token <key>`. Session auth continues to work for logged-in browser clients.
- A dedicated machine user (e.g. `catalog-ssg`) with a provisioned Token becomes the documented way to issue a build credential — one revocable key per consumer, no staff accounts in build envs.
- The view keeps its `pagination_class = None` override; only the permission override (`AllowAny`) is removed.
- Tests updated: anonymous access SHALL now return `401`; requests with a valid token SHALL succeed. The existing "public access" assertions are replaced.
- Tooling/docs updated: Bruno collection and `docs/django-drf.md` reflect that the catalog is authenticated and show how to create the build token in Django admin and wire it into the build environment.
- SSG side (separate Astro repo): build must pass the token header from an env var — tracked as a contract here, implemented in the frontend repo.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `public-catalog-api`: the endpoint requirement changes from "public, unauthenticated" to "authenticated via API key (DRF Token) while keeping the dual Token/Session auth and the unpaginated, single-fetch shape". Requires a delta spec superseding the `Unauthenticated request succeeds` scenario.

## Impact

- **Code**: `artworks/views.py` (remove `AllowAny`), `artworks/tests.py` (replace public-access tests with auth-required + token tests).
- **API surface**: `/api/catalog/` returns `401` for anonymous requests instead of `200`. Payload shape, scoping, and pagination behaviour unchanged.
- **Permissions**: the only `AllowAny` override in the project disappears; every API route now runs under the global `IsAuthenticated` + dual auth.
- **Data**: a new machine user (`catalog-ssg`) + Token; no schema change, no migration.
- **Deployment**: the Astro build environment must hold the token (e.g. `CATALOG_API_TOKEN`); the backend change ships first, so builds after the deploy must already carry the token.
- **Docs**: `docs/django-drf.md` section 6 extended with the build-token provisioning story; `bruno` collection updated.
- **Rollback**: reverting the permission change restores public access without breaking the payload contract.
