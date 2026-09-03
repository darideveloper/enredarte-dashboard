## 1. Serializer — absolute banner_image via get_media_url

- [x] 1.1 Update `blog/serializers.py`: import `get_media_url` from `utils/media.py` and change `PostSummarySerializer.get_banner_image` to `return get_media_url(obj.banner_image) if obj.banner_image else None` (covers both list and detail; verify `PostDetailSerializer` inherits).
- [x] 1.2 Verify no other `banner_image` serialization paths (admin `display_banner` stays raw `obj.banner_image.url` for thumbnail; only API changes).

## 2. Tests — contract absolute + edge cases

- [x] 2.1 Extend `blog/tests.py:BlogAPITestCase` to assert absolute URL: with `override_settings(HOST="https://enredarte-dashboard.apps.darideveloper.com")` list and detail return `banner_image` starting with `HOST` (and containing `banner1`), not relative.
- [x] 2.2 Add S3 pass-through test: mock `Post.banner_image.url` to `https://daridev-django.sfo3.cdn.digitaloceanspaces.com/enredarte/media/blog/banners/banner-1.jpg` and assert `get_media_url` leaves it unchanged (no double HOST) for both endpoints.
- [x] 2.3 Add missing-HOST fallback test: `override_settings(HOST="")` → `banner_image` returns relative `/media/blog/banners/...` without crash.
- [x] 2.4 Keep `null` case: post without `banner_image` still returns `null` (existing post2).

## 3. Bruno collection docs

- [x] 3.1 Update `bruno/collections/enredarte-dashboard-api/Posts/GET list.bru` example `banner_image` from `/media/...` to absolute `{{base_url}}/media/blog/banners/banner-1.jpg` (or `https://.../media/...`) and `docs` to state "absolute URL via get_media_url".
- [x] 3.2 Update `bruno/collections/enredarte-dashboard-api/Posts/GET detail.bru` same.

## 4. Verification

- [x] 4.1 Run `python manage.py test blog --verbosity=2` (and `pytest` if used) — all BlogAPITestCase pass, no N+1 regression.
- [x] 4.2 Manual curl check: `GET /api/blog/posts/` with `HOST` set shows absolute; with S3 storage shows CDN absolute; compare to `artworks` `photo` behavior.
