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
`/apis/artworks/` — one folder per model, each with a `GET list.bru` and a
`GET detail.bru` request (detail uses the ID `1`; change it to any existing record id):

| Model | List URL | Detail URL |
| --- | --- | --- |
| Artists | `GET {{base_url}}/apis/artworks/artists/` | `GET {{base_url}}/apis/artworks/artists/1/` |
| ArtCurators | `GET {{base_url}}/apis/artworks/art-curators/` | `GET {{base_url}}/apis/artworks/art-curators/1/` |
| Locations | `GET {{base_url}}/apis/artworks/locations/` | `GET {{base_url}}/apis/artworks/locations/1/` |
| Galleries | `GET {{base_url}}/apis/artworks/galleries/` | `GET {{base_url}}/apis/artworks/galleries/1/` |
| Disciplines | `GET {{base_url}}/apis/artworks/disciplines/` | `GET {{base_url}}/apis/artworks/disciplines/1/` |
| Techniques | `GET {{base_url}}/apis/artworks/techniques/` | `GET {{base_url}}/apis/artworks/techniques/1/` |
| Themes | `GET {{base_url}}/apis/artworks/themes/` | `GET {{base_url}}/apis/artworks/themes/1/` |
| Formats | `GET {{base_url}}/apis/artworks/formats/` | `GET {{base_url}}/apis/artworks/formats/1/` |
| Scales | `GET {{base_url}}/apis/artworks/scales/` | `GET {{base_url}}/apis/artworks/scales/1/` |
| Artworks | `GET {{base_url}}/apis/artworks/artworks/` | `GET {{base_url}}/apis/artworks/artworks/1/` |

All artworks requests send `Authorization: Token {{token}}`. The router root
`GET {{base_url}}/apis/artworks/` lists the registered endpoints. Every list
response is paginated (`page_size` query param, max 100).

### Blog API (Public)

The Blog API exposes public, read-only endpoints under `/api/blog/posts/` requiring no authentication:

| Resource | List URL | Detail URL |
| --- | --- | --- |
| Posts | `GET {{base_url}}/api/blog/posts/` | `GET {{base_url}}/api/blog/posts/:slug/` |

- `GET list.bru`: Paginated summary listing of active posts.
- `GET detail.bru`: Full post detail lookup by `slug` with bilingual Markdown content.

## Add a new endpoint

Create a `.bru` file under a new or existing folder in this collection, using
only the `{{base_url}}` / `{{token}}` variables (no hard-coded hosts or
credentials).
