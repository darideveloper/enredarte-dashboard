## Context

See `proposal.md` for motivation. The `Post` model currently defines `sort_order = models.IntegerField(default=0, ...)`, which is mapped to database column `sort_order`, exposed in `PostAdmin` with an auto-incrementing `Max` calculation, serialized in `PostSummarySerializer`, and used in `PostViewSet` ordering (`.order_by("-published_at", "sort_order", "-id")`).

## Goals / Non-Goals

**Goals:**
- Remove the `sort_order` field from `Post` model and create a clean database migration.
- Remove `sort_order` display, fieldsets, and form initial calculation from `PostAdmin`.
- Remove `sort_order` from `PostSummarySerializer` and `PostDetailSerializer`.
- Update `PostViewSet` query ordering to `.order_by("-published_at", "-id")`.
- Update `blog/tests.py` test suite to reflect the new schema and ordering contract.

**Non-Goals:**
- Changes to `BlogImage` or `PostTranslation` models (they do not have `sort_order`).
- Adding new ordering fields (chronological sorting via `published_at` and database primary key is the standard).

## Decisions

### 1. Queryset Ordering Strategy
- **Decision**: Update `PostViewSet.get_queryset()` ordering to `.order_by("-published_at", "-id")`.
- **Rationale**: Reverse chronological order (`-published_at`) is the standard for blog feeds. `-id` acts as a deterministic tie-breaker for any posts sharing identical publication timestamps.
- **Alternatives Considered**:
  - `.order_by("-published_at", "-created_at", "-id")`: Redundant because `id` autoincrements sequentially with creation.

### 2. Admin Form Initial Data Simplification
- **Decision**: Retain `initial["published_at"] = timezone.now()` in `PostAdmin.get_changeform_initial_data()` and remove the `Max("sort_order")` query entirely. Also remove the unused `Max` import from `django.db.models`.
- **Rationale**: Eliminates an unnecessary aggregation query on every post add-form rendering.

### 3. Database Migration Path
- **Decision**: Create Django migration `0003_remove_post_sort_order.py` with a single `migrations.RemoveField(model_name='post', name='sort_order')` operation.
- **Rationale**: Standard, backward-compatible migration strategy without table recreation or data loss for other fields.

## Risks / Trade-offs

- **[Risk] Breaking API Change for Frontend Clients**: Frontend consumers expecting `sort_order` in the JSON response will no longer receive this key.
  - **Mitigation**: Blog posts are returned already ordered in the JSON array; frontend clients simply iterate over the array without manual client-side sorting.
- **[Risk] Test Failures**: Existing tests in `blog/tests.py` instantiate `Post` with `sort_order` kwargs and assert its ordering.
  - **Mitigation**: Update all test factories, test fixtures, and assertions in `blog/tests.py` as part of this change.

## Migration Plan

1. Apply migration `blog/migrations/0003_remove_post_sort_order.py` (`python manage.py migrate blog`).
2. Run test suite to verify zero regressions.
