# Bruno Workspace — Enredarte Dashboard API

Git-native [Bruno](https://www.usebruno.com/) workspace for exercising the DRF
API (`docs/django-drf.md`). Workspaces are the Bruno 3.0+ container; this one
holds the `Enredarte Dashboard API` collection under `collections/`. Every
request is a plain-text `.bru` file, so edits are reviewable and diffable in
code review.

## Prerequisites

- [Bruno desktop](https://www.usebruno.com/downloads) installed.
- Dev server running: `./dev.sh`. The collection targets the portless subdomain
  `https://enredarte-dashboard.localhost` (derived from the project dir name by
  `dev.sh`/`portless`), so the proxy must be up. If it is not running, requests
  fail with a connection error — that is a proxy issue, not a Bruno
  misconfiguration.
- Fallback URL: `http://localhost:8000` only works when port 8000 is free
  (`dev.sh` auto-increments to the next free port on conflict).

## Open the workspace

1. In Bruno, click **WorkSpace dropdown → Open workspace** and select this
   `bruno/` folder (the one containing `workspace.yml`).
2. In the top-right environment dropdown, pick **dev**.

## Get a DRF Token

Tokens are not exposed through a login endpoint. Create one from the Django
shell (`docs/django-drf.md`, section 6):

```sh
python manage.py shell
```

```python
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User

user = User.objects.get(username="admin")
token, created = Token.objects.get_or_create(user=user)
print(token.key)
```

Copy `collections/enredarte-dashboard-api/environments/dev.bru.example` to
`dev.bru` (the `.bru` file is gitignored) and paste the printed key as the
`token` value. Never commit a real token — only the `.bru.example` template with
a placeholder is tracked.

## Requests

### Artworks API (Authenticated)

The Artworks API exposes 10 per-model, read-only, paginated endpoints under
`/api/artworks/` — one folder per model, each with a `GET list.bru` and a
`GET detail.bru` request (detail uses the ID `1`; change it to any existing record id):

| Model | List URL | Detail URL |
| --- | --- | --- |
| Artists | `GET {{base_url}}/api/artworks/artists/` | `GET {{base_url}}/api/artworks/artists/1/` |
| ArtCurators | `GET {{base_url}}/api/artworks/art-curators/` | `GET {{base_url}}/api/artworks/art-curators/1/` |
| Locations | `GET {{base_url}}/api/artworks/locations/` | `GET {{base_url}}/api/artworks/locations/1/` |
| Galleries | `GET {{base_url}}/api/artworks/galleries/` | `GET {{base_url}}/api/artworks/galleries/1/` |
| Disciplines | `GET {{base_url}}/api/artworks/disciplines/` | `GET {{base_url}}/api/artworks/disciplines/1/` |
| Techniques | `GET {{base_url}}/api/artworks/techniques/` | `GET {{base_url}}/api/artworks/techniques/1/` |
| Themes | `GET {{base_url}}/api/artworks/themes/` | `GET {{base_url}}/api/artworks/themes/1/` |
| Formats | `GET {{base_url}}/api/artworks/formats/` | `GET {{base_url}}/api/artworks/formats/1/` |
| Scales | `GET {{base_url}}/api/artworks/scales/` | `GET {{base_url}}/api/artworks/scales/1/` |
| Artworks | `GET {{base_url}}/api/artworks/artworks/` | `GET {{base_url}}/api/artworks/artworks/1/` |

All artworks requests send `Authorization: Token {{token}}`. The router root
`GET {{base_url}}/api/artworks/` lists the registered endpoints. Every list
response is paginated (`page_size` query param, max 100).

> **Exception — public view counter:** the `Artworks/` folder also holds
> `POST visit.bru` (`POST {{base_url}}/api/artworks/artworks/:slug/visit/`),
> which records an artwork view (`views_count` +1, returns the new count).
> Like `Sales/`, it is public (no `Authorization` header) and throttled
> (`artwork_views` 20/hour per client).

### Blog API (Public)

The Blog API exposes public, read-only endpoints under `/api/blog/posts/` requiring no authentication:

| Resource | List URL | Detail URL |
| --- | --- | --- |
| Posts | `GET {{base_url}}/api/blog/posts/` | `GET {{base_url}}/api/blog/posts/:slug/` |

- `GET list.bru`: Paginated summary listing of active posts.
- `GET detail.bru`: Full post detail lookup by `slug` with bilingual Markdown content.

### Sales API (Public)

The Sales API exposes the artwork purchase flow under `/api/artworks/`
(first public, first write endpoints in this collection) — no
authentication, no `Authorization` header, no token needed. Run the
requests top-to-bottom in the `Sales/` folder order:

| # | Request | URL |
| --- | --- | --- |
| 23 | `POST buy` | `POST {{base_url}}/api/artworks/artworks/obra-ejemplo/buy/` |
| 24 | `GET order-summary` | `GET {{base_url}}/api/artworks/orders/0123456789ab/` |
| 25 | `POST order-delivery` | `POST {{base_url}}/api/artworks/orders/0123456789ab/delivery/` |

- `POST buy`: reserve + start Checkout. Body `{currency: mxn|usd, email}`.
  Replace `obra-ejemplo` with a real artwork slug. Returns `{checkout_url}`
  (`201` new reservation, `200` same buyer re-click). Each `docs` block
  lists the full status matrix (201/200/400/404/409/502/503/429).
- Slug handoff: buy returns only `{checkout_url}` — the order slug is NOT
  in the response. Pay (or copy `?order=` from the Stripe success redirect
  `{PUBLIC_SITE_URL}/compra-exitosa/?order={slug}`), then paste the real
  slug into the next two requests. The fake-hex placeholders never return
  `200` — replace the slug, then Send.
- `GET order-summary`: 8-field summary for the success page (`200` for paid
  orders; `404` while unpaid → poll every 3s, up to ~60s).
- `POST order-delivery`: delivery form (9 required + 5 optional fields).
  `200` saves, `409` means already submitted (treat as success).
- Throttles: `artwork_buys` 20/hour (buy), `artwork_orders` 60/hour
  (summary + delivery). Full flow details: `docs/artwork-sales.md`.

## Smoke test (headless, no credentials)

Sales endpoints are public, so the flow doubles as a credential-free smoke
test (documented here only — no script file, no CI wiring). Needs the dev
server running (`./dev.sh`). Run from the collection folder (the CLI only
runs at a collection root); `--insecure` is required because the portless
proxy serves a self-signed certificate:

```sh
cd collections/enredarte-dashboard-api
npx @usebruno/cli run Sales/ --env dev --insecure
```

Accepted outcomes (any dev DB state stays green):

- `POST buy` → `201` (fresh reservation) or `409` (already reserved/sold)
  with a real artwork slug; `404` with the committed example slug
  (`obra-ejemplo` unknown in that DB — benign, proves routing + envelope)
- `GET order-summary` → `200` (paid order) or `404` (fake-hex placeholder)
- `POST order-delivery` is excluded by design (needs a real paid order —
  exercise it manually after a test purchase)

## Add a new endpoint

Create a `.bru` file under a new or existing folder in this collection, using
only the `{{base_url}}` / `{{token}}` variables (no hard-coded hosts or
credentials).
