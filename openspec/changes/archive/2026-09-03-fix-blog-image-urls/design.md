## Context

`blog` exposes `GET /api/blog/posts/` and `GET /api/blog/posts/{slug}/` via `PostSummarySerializer` / `PostDetailSerializer` (`blog/serializers.py:11`). Today `get_banner_image` returns `obj.banner_image.url` verbatim. In local dev (`STORAGE_AWS=False`) that's `/media/blog/banners/...`; in prod (`STORAGE_AWS=True`, `PublicMediaStorage` on DO Spaces) it's `https://daridev-django.sfo3.cdn.digitaloceanspaces.com/enredarte/media/blog/banners/...` plus `AWS_S3_CUSTOM_DOMAIN`. `artworks` app normalizes all image fields through `utils/media.py:get_media_url` (`artworks/serializers.py:28`) which prefixes `settings.HOST` for relative URLs and passes S3 URLs through (`s3.amazonaws.com` / `digitaloceanspaces` check). Frontend currently does `HOST + banner_image` assuming relative; with absolute S3 value in prod it produces doubled host `https://dashboard...https://cdn...`.

`utils/media.py:5` handles: `if not s3/digitaloceanspaces` and `HOST` contains `://` → `f"{HOST}{url}"`, else return as-is. Missing `HOST` → relative fallback. Same logic is used by `BlogImageAdmin.change_view` (`blog/admin.py:123`) for admin copy-link.

Stakeholders: frontend (landing/SSR consuming blog API), backend (blog, artworks, utils), Bruno docs.

## Goals / Non-Goals

**Goals:**
- Make `banner_image` contract absolute (via `get_media_url`) for both list and detail, identical to `artworks-rest-api`.
- Eliminate frontend need to prefix `HOST`; one field is directly usable as `<img src>`.
- Keep S3 pass-through behavior and relative fallback when `HOST` empty (testable).
- Update Bruno collection examples/docs and tests to new contract.

**Non-Goals:**
- Changing storage backends or `HOST` env vars.
- Rewriting inline markdown image URLs inside `PostTranslation.content` (`/media/blog/images/...`). Those stay relative text for now; separate concern.
- Adding new endpoint for `BlogImage` standalone.
- Modifying `BlogImage` model/admin beyond reusing `get_media_url` already there.

## Decisions

1. **Reuse `get_media_url` in `blog/serializers.py`** (Decision over duplicating logic):
   - `from utils.media import get_media_url; def get_banner_image -> get_media_url(obj.banner_image) if obj.banner_image else None` mirroring `artworks/serializers.py:_absolute_url`. Alternatives: construct absolute in serializer with `request.build_absolute_uri` — rejected: would couple to request, diverge from artworks, and break `HOST` env precedence (`project/settings.py:11` `override=True`). `get_media_url` already covers local vs S3 and is spec'd in `artworks-rest-api`.
   - Trade: `get_media_url` checks string containment `digitaloceanspaces` / `s3.amazonaws.com`; if custom CDNs without those substrings appear, it would prefix incorrectly. Acceptable — matches current artworks risk; adding `AWS_S3_CUSTOM_DOMAIN` check would be follow-up.

2. **Single code path via `PostSummarySerializer`**:
   - Change only `PostSummarySerializer.get_banner_image`; `PostDetailSerializer` inherits, so both endpoints fixed in one line. Alternatives: add separate fields — unnecessary.

3. **Bruno docs alignment**:
   - Update `GET list.bru` / `GET detail.bru` `docs` block and example JSON `banner_image` to absolute form (`{{hostOrS3}}/media/...`). Keeps contract visible to consumers.

4. **Testing strategy**:
   - Extend `blog/tests.py` (mirrors `artworks` tests): cases `test_banner_image_is_absolute_with_host`, `test_banner_image_s3_pass_through`, `test_banner_image_relative_when_host_empty`, parametrized for list and detail. Use `override_settings(HOST=...)` and mock `SimpleUploadedFile` / `FieldFile.url` to S3 URL. Keep `test_list_posts_success` updating expectation to contain Host.

## Risks / Trade-offs

- [Breaking change] Clients that still do `HOST + banner_image` will double-host until they remove prefix → Mitigation: document BREAKING in proposal, frontend guard `if (/^https?:\/\//.test(url)) return url`, coordinate deploy.
- [Empty HOST] Returns relative `/media/...` — frontend must handle relative fallback (same as artworks). → Mitigation: test ensures no crash; frontend same guard handles fallback via prefix.
- [CDN substring miss] Custom domain not containing `digitaloceanspaces` would be prefixed → Mitigation: noted as known ceiling (`# ponytail: substring check`), add domain list later if needed.

## Migration Plan

1. Deploy backend with serializer change (1 line + import). No migration.
2. Update frontend to use `banner_image` as-is (remove `HOST +`, optional guard).
3. Update Bruno collection.
4. Verify `curl /api/blog/posts/` vs `artworks` in both envs.
5. Rollback: revert single line; frontend re-add prefix if needed — no data migration.

## Open Questions

- Should markdown `content_es/en` inline image URLs also be absolutized server-side (post-process markdown or store absolute)? Deferred — requires HTML/markdown transform, out of scope for this minimal fix.
- Do we want `get_media_url` to accept `AWS_S3_CUSTOM_DOMAIN` explicitly instead of substring check? Track as follow-up if new CDN appears.
