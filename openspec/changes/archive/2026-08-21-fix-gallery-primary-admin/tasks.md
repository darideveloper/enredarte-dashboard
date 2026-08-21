## 1. Admin form fix

- [x] 1.1 Add a `GalleryAdminForm(forms.ModelForm)` in `artworks/admin.py` whose `clean()` sets `is_primary=False` on any other primary gallery (via `Gallery.objects.filter(is_primary=True).exclude(pk=self.instance.pk).update(is_primary=False)`) when the submitted `is_primary=True`, before returning cleaned data.
- [x] 1.2 Wire the form into `GalleryAdmin` by setting `form = GalleryAdminForm` (add the necessary `from django import forms` import if not already present).

## 2. Regression tests

- [x] 2.1 In `GalleryAdminTestCase` (`artworks/tests.py`), add a test that creates a primary gallery A and a second gallery B, then POSTs the admin change form for B against `admin:artworks_gallery_change` with `is_primary=True` plus the required inline data for the Gallery change form (both `translations` es/en rows and an empty `artwork_links` formset management form, following the existing `TranslationInlineEnforcementTestCase` POST pattern), asserting the response is a redirect (302) away from the change page, A is no longer primary, B is primary, and exactly one primary `Gallery` exists.
- [x] 2.2 Add a companion assertion that the change form alone (not the full request) is valid: build `GalleryAdminForm` (or `self.gallery_admin.get_form(request)`) bound with `is_primary=True` for B and assert `form.is_valid()` is `True` after the fix.
- [x] 2.3 Add a test that POSTs the admin add form for a brand-new gallery with `is_primary=True` (plus valid es/en translation rows and an empty `artwork_links` formset), asserting the response is a redirect, the previous primary A is unmarked, the new gallery is primary, and exactly one primary `Gallery` exists.
- [x] 2.4 Verify the existing model-level tests still pass unchanged, especially `test_flagging_second_unflags_first` and `test_db_rejects_second_primary` (ORM `save()` and `bulk_create()` backstop behavior must remain intact).

## 3. Verification

- [x] 3.1 Run the gallery-related tests (`manage.py test artworks.tests.GalleryAdminTestCase artworks.tests.GalleryPrimaryFlagModelTestCase` or the full `artworks` suite) and confirm all pass.
- [x] 3.2 Reproduce the original bug scenario manually through the admin UI (mark a second gallery primary) and confirm the first is unmarked and the save succeeds with no `unique_primary_gallery` error.
- [x] 3.3 Run the lint/typecheck command used by the project (check `dev.sh` / project docs for the convention) and confirm no new violations.