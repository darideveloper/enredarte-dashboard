## 1. Database & Model Layer

- [x] 1.1 Remove `sort_order` field definition from `Post` model in `blog/models.py` and verify `Post` model inspection
- [x] 1.2 Create and apply database migration `0003_remove_post_sort_order.py` in `blog/migrations/` and verify migration applies cleanly

## 2. Admin Interface

- [x] 2.1 Remove `sort_order` from `fieldsets` and `list_display` in `PostAdmin` within `blog/admin.py` and verify admin registration
- [x] 2.2 Remove `sort_order` auto-increment calculation and unused `Max` aggregate in `PostAdmin.get_changeform_initial_data()`

## 3. Serializers & Views (API Layer)

- [x] 3.1 Remove `sort_order` field from `PostSummarySerializer` in `blog/serializers.py` and verify serialization shape
- [x] 3.2 Update `PostViewSet.get_queryset()` ordering in `blog/views.py` to `.order_by("-published_at", "-id")`

## 4. Tests & Verification

- [x] 4.1 Update `blog/tests.py` to remove `sort_order` attributes and update ordering assertions
- [x] 4.2 Run test suite across `blog` and run `openspec validate --change remove-post-sort-order`
