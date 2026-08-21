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

Paste the printed key into `collections/enredarte-dashboard-api/environments/dev.bru`
as the `token` value. Never commit a real token — the file ships with a
placeholder.

## Requests

| Request | URL | Auth |
| --- | --- | --- |
| Public Catalog | `GET {{base_url}}/api/catalog/` | none |
| API Root | `GET {{base_url}}/api/` | `Authorization: Token {{token}}` |

## Add a new endpoint

Create a `.bru` file under a new or existing folder in this collection, using
only the `{{base_url}}` / `{{token}}` variables (no hard-coded hosts or
credentials).
