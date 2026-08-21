## 1. Post Admin Implementation

- [x] 1.1 Create `static/js/blog_slug_autofill.js` for real-time slug auto-population from Spanish title input
- [x] 1.2 Implement `PostTranslationInline` using `StackedInline` and `TranslationInlineFormSet` in `blog/admin.py`
- [x] 1.3 Implement `PostAdmin` with `get_changeform_initial_data` (`published_at = now`, `sort_order = max + 1`), banner thumbnail/preview, `date_hierarchy`, structured fieldsets, search, and filters in `blog/admin.py`

## 2. BlogImage Admin Implementation

- [x] 2.1 Implement `BlogImageAdmin` with `sidebar_icon = "image"`, `list_per_page = 25`, `date_hierarchy = "created_at"`, dual thumbnail previews, and `copy_link` action in `blog/admin.py`

## 3. Verification

- [x] 3.1 Verify admin registrations, initial form data pre-fills, live slug auto-population, copy link action, and query efficiency
