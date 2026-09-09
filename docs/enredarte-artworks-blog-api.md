---
created: 2026-09-09
updated: 2026-09-09
tags:
  - enredarte
  - api
  - artworks
  - blog
type: guide
status: active
---

# Enredarte Artworks & Blog API

Project-specific API reference for the two routers in `project/urls.py`. Global envelope and auth come from `project/settings.py` (`CustomPageNumberPagination`, Token+Session auth, `IsAuthenticated` default, custom exception handler) — see [[django-drf\|DRF Implementation Guide]].

## Routers

| Router | Prefix | Auth | Lookup |
|---|---|---|---|
| artworks | `/api/artworks/` | `Authorization: Token <key>` required | ID (`artworks/1/`) |
| blog | `/api/blog/` | public, no header | slug (`posts/<slug>/`) |

## Artworks endpoints (10 resources + router root, all authenticated)

- `GET /api/artworks/` — router root
- `GET /api/artworks/artists/` — only `is_active` artists are meaningful to the landing; the endpoint itself lists rows (visibility is driven by webhooks, not by the view)
- `GET /api/artworks/art-curators/`
- `GET /api/artworks/locations/`
- `GET /api/artworks/galleries/`
- `GET /api/artworks/disciplines/`
- `GET /api/artworks/techniques/`
- `GET /api/artworks/themes/`
- `GET /api/artworks/formats/`
- `GET /api/artworks/scales/`
- `GET /api/artworks/artworks/`

List responses use the paginated envelope (`count`, `next`, `previous`, `page`, `page_size`, `total_pages`, `results`); `page_size` query param, max 100. Translations nest as `{language: {field: value}}` dicts (`es`/`en`); related models are `{id, slug}` references; artwork images are absolute URLs (see `utils/media.py:get_media_url` + `HOST`).

## Blog endpoints (public)

- `GET /api/blog/posts/` — list (no auth)
- `GET /api/blog/posts/<slug>/` — detail (no auth)

Posts carry nested translations; `BlogImage` rows expose absolute image URLs with an admin copy-link button (see [[django-image-copy-link\|Image Copy Link]]). The admin auto-fills the slug from the title via `static/js/blog_slug_autofill.js`; `static/js/script.js` holds project-wide JS.

## Manual exercise

Use the Bruno workspace (`bruno/`, see [[django-bruno\|Bruno API Client Guide]]): one folder per model with `GET list.bru` + `GET detail.bru`, `{{base_url}}` + `{{token}}` from the active environment. `Posts/` needs no token.

## See also

- [[enredarte-overview\|Enredarte Overview]]
- [[stripe-subscriptions\|Stripe Artist Subscriptions]] (what drives `is_active`)
