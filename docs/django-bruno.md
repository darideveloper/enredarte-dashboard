---
created: 2026-08-12
updated: 2026-08-12
tags:
  - bruno
  - api-client
  - rest
  - documentation
type: resource
status: active
---

# Bruno API Client Guide

This document is a reusable blueprint for wiring **Bruno** into any Django (or any other) project so the team can exercise a REST API manually with a git-native, version-controlled collection. It covers the Bruno 3.0+ **workspace** layout, the `.bru` request format, environments, DRF Token authentication, and the pitfalls that surfaced while building the collection in this repo (`bruno/`).

Bruno is chosen over Postman because it is open-source and stores collections as plain-text `.bru` files in the repo — no cloud lock-in, no proprietary sync, full diffability in code review.

---

## 1. Prerequisites

- **Bruno desktop** (3.0+) installed — downloads at [usebruno.com](https://www.usebruno.com/downloads). Workspaces are only available in 3.0.0 and higher.
- A dev server reachable over the local network. In this repo that is the portless subdomain `https://<project-dir-name>.localhost` started by `./dev.sh` — see [[django-local-subdomain-setup|Local Development & Subdomain Setup]].
- Fallback URL: `http://localhost:8000` only works when port 8000 is free (`dev.sh` auto-increments to the next free port on conflict).

---

## 2. Directory structure

A Bruno **workspace** is a folder with `workspace.yml` at its root; collections live under `collections/`. The layout used in this repo:

```
bruno/
├── workspace.yml                        # workspace root config (REQUIRED)
└── collections/
    └── <collection-name>/               # one folder per collection
        ├── bruno.json                   # collection metadata
        ├── environments/dev.bru        # environment variables (gitignored; dev.bru.example is the tracked template)
        ├── Artists/
        │   ├── GET list.bru
        │   └── GET detail.bru          # request files
        └── Artworks/
            ├── GET list.bru
            └── GET detail.bru
```

- Area folders under the collection root (`Artists/`, `Artworks/`, …) are plain subdirectories; Bruno uses them to group requests.
- A per-folder `folder.bru` file is optional — only needed when a folder carries its own settings/auth/scripts. None of the folders here need it.
- A `collection.bru` file is also optional — it only carries collection-level settings (e.g. pre-request scripts). `bruno.json` alone is enough for this setup.

---

## 3. Workspace config: `bruno/workspace.yml`

```yaml
opencollection: 1.0.0
info:
  name: "Enredarte Dashboard"
  type: workspace

collections:
  - name: "Enredarte Dashboard API"
    path: "collections/enredarte-dashboard-api"
```

- `opencollection: 1.0.0` is the **OpenCollection spec version** (the standard Bruno uses), not the Bruno app version.
- `path` is relative to the workspace root and must point at the collection folder.
- Add more entries under `collections:` to host multiple collections in one workspace.

---

## 4. Collection config: `bruno/collections/<name>/bruno.json`

```json
{
  "version": "1",
  "name": "Enredarte Dashboard API",
  "type": "collection"
}
```

- `"version": "1"` here is the **collection file-format version** — a different concept from the `opencollection` version in `workspace.yml`. Keep it as `"1"`.
- `name` and the `path` in `workspace.yml` are project-specific; replace them when bootstrapping a new project.

---

## 5. Environments: `bruno/collections/<name>/environments/<env>.bru`

Environments parameterize requests so no hard-coded host or credential appears in request files. The **display name of the environment is the file basename** (e.g. `dev.bru` shows as **dev**), so rename the file, not a field.

```bru
vars {
  @description('''Base URL of the local dev server, reachable via the portless subdomain started by ./dev.sh. Fallback: http://localhost:8000 (only usable when port 8000 is free).''')
  base_url: https://enredarte-dashboard.localhost

  @description('''DRF Token placeholder. Mint a real token from the Django shell (see docs/django-drf.md, section 6) and paste it here. Never commit a real token.''')
  token: <paste-token-here>
}
```

- Variables are declared in a `vars { ... }` block and referenced as `{{var_name}}`.
- `@description('''...''')` documents a variable; the `'''...'''` form supports multiline strings, while `@description("...")` is the single-line variant.
- Adding `dev`, `prod`, or `staging` environments is a **one-file copy** of this template with new values.

> **Security note:** environment files (e.g. `dev.bru`) hold real tokens and are gitignored — never commit them. The committed template is the `dev.bru.example` sibling: copy it to `dev.bru`, paste a real token, and keep the `.bru` file local. Because the template is committed as `.example`, every clone gets the placeholder with no risk of committing a live credential.

---

## 6. Request files: `.bru`

Each request is a single `.bru` file. Every request begins with a `meta` block (`seq` orders the tab) followed by an HTTP method block.

### 6.1 Authenticated GET — DRF Token header (per-model list)

Every endpoint under `/apis/artworks/` requires authentication. DRF uses `Authorization: Token <key>`; the scheme is a bare word, so the header is set explicitly rather than via a bearer-blanket auth preset. The collection ships one folder per model, each with `GET list.bru` and `GET detail.bru` (e.g. the artworks list):

```bru
meta {
  name: GET list
  type: http
  seq: 1
}

get {
  url: {{base_url}}/apis/artworks/artworks/
  body: none
  auth: none
}

headers {
  Authorization: Token {{token}}
}
```

### 6.2 Authenticated GET — DRF Token header (router root)

```bru
meta {
  name: GET api root
  type: http
  seq: 2
}

get {
  url: {{base_url}}/apis/artworks/
  body: none
  auth: none
}

headers {
  Authorization: Token {{token}}
}
```

### 6.3 POST with JSON body

A POST needs **two blocks**: the `post` method block sets `body: json`, then a separate `body:json` block holds the payload.

```bru
meta {
  name: Create thing
  type: http
  seq: 3
}

post {
  url: {{base_url}}/api/thing/
  body: json
  auth: none
}

body:json {
  {
    "name": "example",
    "active": true
  }
}
```

Other request types follow the same shape (`put`, `patch`, `delete`) with their own block names.

---

## 7. Opening the workspace

1. In Bruno, click **Workspace dropdown → Open workspace**.
2. Select the folder containing `workspace.yml` (in this repo, `bruno/`).
3. Pick the active environment in the top-right environment dropdown (e.g. **dev**).

> **Pitfall:** opening a *bare collection folder* (one with `bruno.json` but no `workspace.yml`) produces `Invalid workspace: workspace.yml not found`. The folder must be structured as a workspace, or opened through the collection flow instead.

---

## 8. Running a request

1. Ensure the prerequisites are up (dev server/proxy running, real token in the selected environment).
2. Click the **Send** button on a request tab.
3. Read the response in the output panel; the request keeps whatever environment was selected at send time.

If the request fails with a *connection error* while the proxy is down, that is an environment issue (the portless subdomain is not mapped by `dev.sh`), not a Bruno misconfiguration.

---

## 9. Adding endpoints & environments

- **New request:** create a `.bru` file under a new or existing area folder in the collection, referencing only `{{base_url}}` / `{{token}}` (never hard-coded hosts or credentials). Assign the next `seq`.
- **New environment:** copy `dev.bru.example` to `dev.bru` (or `prod.bru` / `staging.bru`), paste the real token, and edit the values; `workspace.yml` needs no change for collection-level environments.

---

## 10. Minting a DRF Token

DRF exposes no login endpoint (see [[django-drf|DRF Implementation Guide]] §6 for the full context). Tokens are created manually in the Django shell:

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

Paste the printed key into the `token` variable of the active environment. Never commit it.

---

## 11. CI / automation (follow-up)

This guide does not automate Bruno. When the API grows a login/token endpoint, the top follow-ups are:

- A Bruno pre-request `script: js` block that mints a token at runtime (currently impossible: no login endpoint exists).
- `bru run` smoke tests wired into CI — deferred, not part of the initial setup.

---

## 12. Pitfalls & lessons learned

- **`Invalid workspace: workspace.yml not found`** — the folder must be opened as a workspace at the `workspace.yml` level, not at a standalone collection.
- **Environment name = file basename** — renaming `local.bru` → `dev.bru` is how you rename an environment; there is no in-file name field.
- **Subdomain derives from the project dir name**, not from any `HOST` env var: with the repo folder named `enredarte-dashboard`, the portless URL is `https://enredarte-dashboard.localhost`, even though both subdomains sit in `ALLOWED_HOSTS`.
- **Environment files are gitignored; the template is committed as `.example`** — copy `dev.bru.example` to `dev.bru` and paste a real token locally; never commit the `.bru` file itself.
- **Two different `version` concepts** — `opencollection: 1.0.0` (spec version in `workspace.yml`) vs `"version": "1"` (file format version in `bruno.json`).
- **`.bru` format drifts across Bruno versions** — files are plain text, so a Bruno upgrade that changes the format is a small, reviewable diff.