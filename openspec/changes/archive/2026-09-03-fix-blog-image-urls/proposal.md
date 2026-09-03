## Why

Frontend receives `banner_image` URLs like `https://enredarte-dashboard.apps.darideveloper.comhttps://daridev-django.sfo3.cdn.digitaloceanspaces.com/enredarte/media/blog/banners/banner-1.jpg` — doubled host. Investigation shows `blog/serializers.py:get_banner_image` returns `obj.banner_image.url` verbatim (relative locally, absolute S3 in prod) while `artworks` serializers use `utils/media.py:get_media_url` to return **absolute URLs** consistently. Frontend naively prefixes `HOST` assuming relative, creating double-host in prod when value is already `https://...cdn.digitaloceanspaces.com/...`. Need backend to provide a single contract: all blog image URLs are absolute via `get_media_url`, eliminating frontend prefix logic and aligning blog with artworks.

## What Changes

- Update `PostSummarySerializer.get_banner_image` (which `PostDetailSerializer` inherits) to return `get_media_url(obj.banner_image)` instead of `obj.banner_image.url`, matching `artworks` pattern (`_absolute_url`).
- Ensure `HOST` handling for local/S3 matches `artworks-rest-api` spec: local → `HOST + /media/...`, S3/DigitalOcean → pass-through, missing `HOST` → relative fallback.
- Update Bruno `Posts/GET list.bru` and `Posts/GET detail.bru` examples/docs to reflect absolute URL contract.
- Add/adjust tests: verify absolute URLs when `HOST` set, S3 pass-through, relative fallback when `HOST` empty, and that both list and detail endpoints return absolute `banner_image`.

## Capabilities

### New Capabilities
- none — reuses existing `blog-apis` capability.

### Modified Capabilities
- `blog-apis`: Change `banner_image` field requirement from relative/verbatim to absolute via `get_media_url` (parity with `artworks-rest-api: Image URLs use get_media_url`).

## Impact

- Affected code: `blog/serializers.py`, `blog/tests.py`, `bruno/collections/enredarte-dashboard-api/Posts/*.bru`, `utils/media.py` (no change, just reused).
- API: `GET /api/blog/posts/` and `GET /api/blog/posts/{slug}/` — **BREAKING** for clients that prefix `HOST` themselves. Frontend must switch to using `banner_image` as-is (guard `^https?://` if kept). Artworks clients unaffected.
- Dependencies: `project/settings.py:HOST` already defined.
- Inline markdown images inside `PostTranslation.content` (`/media/blog/images/...`) remain relative inside markdown — out of scope for this change; addressed separately if needed.
