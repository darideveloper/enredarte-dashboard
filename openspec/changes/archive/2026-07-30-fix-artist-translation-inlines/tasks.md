## 1. Inline Formset & Dynamic Extra Configuration

- [x] 1.1 Implement `ArtistTranslationFormSet` in `artworks/admin.py` to auto-populate default initial language selections (`es` for row 1, `en` for row 2).
- [x] 1.2 Override `get_extra()` and `max_num` on `ArtistTranslationInline` in `artworks/admin.py` to dynamically adjust extra forms based on existing record counts.

## 2. Unit Testing & Verification

- [x] 2.1 Update `artworks/tests.py` to verify initial languages (`es` and `en`) on new artist creation forms.
- [x] 2.2 Add unit test verifying editing an artist with 2 existing translations renders zero extra blank forms.
- [x] 2.3 Run full test suite with `venv/bin/python manage.py test`.
