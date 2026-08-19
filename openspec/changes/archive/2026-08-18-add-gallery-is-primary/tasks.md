## 1. Model

- [x] 1.1 Add `is_primary = models.BooleanField(default=False, verbose_name="Galería principal")` to the `Gallery` model in `artworks/models.py`
- [x] 1.2 Add a `save()` override on `Gallery` that, when `self.is_primary` is `True`, sets `is_primary=False` on all other galleries before saving
- [x] 1.3 Add a database-level conditional unique constraint to `Gallery.Meta.constraints`: `UniqueConstraint(fields=["is_primary"], condition=Q(is_primary=True), name="unique_primary_gallery")`

## 2. Migration

- [x] 2.1 Run `python manage.py makemigrations artworks` and review the generated migration
- [x] 2.2 Apply the migration with `python manage.py migrate`

## 3. API Serializer

- [x] 3.1 Add `"is_primary"` to `GallerySerializer.Meta.fields` in `artworks/serializers.py`

## 4. Admin

- [x] 4.1 Add `is_primary` to the "Información básica" fieldset of `GalleryAdmin` in `artworks/admin.py`
- [x] 4.2 Add `is_primary` to `GalleryAdmin.list_display`
- [x] 4.3 Add `is_primary` to `GalleryAdmin.list_filter`

## 5. Tests

- [x] 5.1 Add model tests: `is_primary` defaults to `False`; setting it to `True` un-sets other galleries
- [x] 5.2 Add a DB-level test asserting that writing a second gallery with `is_primary=True` (bypassing `save()`) raises an `IntegrityError` from the unique constraint
- [x] 5.3 Add serializer test asserting `is_primary` appears in the gallery API response
- [x] 5.4 Add admin tests asserting `is_primary` appears in the GalleryAdmin fieldset, `list_display`, and `list_filter`
- [x] 5.5 Run the full `artworks` test suite and confirm it passes
