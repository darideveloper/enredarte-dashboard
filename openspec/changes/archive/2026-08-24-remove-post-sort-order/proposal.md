## Why

The `sort_order` field on the `Post` model is redundant and unused. Blog posts are naturally organized chronologically by `published_at`, which renders manual integer ordering dead weight. Removing `sort_order` eliminates unnecessary database queries (`Max("sort_order")` on post creation), cleans up the admin interface, aligns with the earlier project-wide removal of unused sort order (`2026-08-18-remove-unused-sort-order`), and removes clutter from public API payloads.

## What Changes

- **BREAKING**: Remove the `sort_order` field from the `Post` model in `blog/models.py`.
- Generate a new database migration (`0003_remove_post_sort_order.py`) to drop the `sort_order` column from the `blog_post` table.
- Remove `sort_order` from `PostAdmin` in `blog/admin.py`: remove it from `fieldsets`, remove it from `list_display`, and remove the `sort_order` auto-increment calculation and `Max` aggregate in `get_changeform_initial_data()`.
- **BREAKING**: Remove `sort_order` from `PostSummarySerializer` (and `PostDetailSerializer`) in `blog/serializers.py`.
- Update `PostViewSet` in `blog/views.py` to order posts strictly by descending publication date and descending ID (`.order_by("-published_at", "-id")`).
- Update test cases in `blog/tests.py` to remove `sort_order` definitions and verify the updated ordering behavior.
- Update the relevant specification files: `blog-models`, `blog-admin`, and `blog-apis`.

## Capabilities

### New Capabilities

None — this is a simplification and removal refactor.

### Modified Capabilities

- `blog-models`: The `Post` model definition no longer contains a `sort_order` field.
- `blog-admin`: `PostAdmin` no longer manages, displays, or auto-calculates `sort_order`.
- `blog-apis`: Public blog API responses omit the `sort_order` field from serialized outputs, and list ordering is governed by `-published_at, -id`.

## Impact

- **Code**: `blog/models.py`, `blog/admin.py`, `blog/serializers.py`, `blog/views.py`, `blog/tests.py`.
- **Database**: New migration removing column `sort_order` from `blog_post`.
- **API**: Breaking response contract change — `sort_order` will no longer be present in `GET /api/blog/posts/` and `GET /api/blog/posts/{slug}/` responses.
- **Specifications**: Live OpenSpec delta specifications for `blog-models`, `blog-admin`, and `blog-apis`.
