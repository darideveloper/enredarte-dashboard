## 1. Artist changelist columns (`artworks/admin.py`)

- [x] 1.1 Reorder `ArtistAdmin.list_display` to `display_name, display_email, display_active, subscription_status_badge, display_artworks_count, display_available_count, display_galleries_count` (drop `birth_year`, `death_year`, `display_techniques_count`, `display_highlighted_count`).
- [x] 1.2 Verify via `git diff` that only `list_display` hunks changed in `ArtistAdmin` and confirm the Resumen fieldset still renders on the change form.

## 2. Artwork changelist columns (`artworks/admin.py`)

- [x] 2.1 Reorder `ArtworkAdmin.list_display` to `display_image, display_title, status, display_active, artist, display_taxonomies, display_price, is_highlighted` (drop `views_count`).
- [x] 2.2 Truncate `display_taxonomies` to ~60 chars with ellipsis in the list (full text stays on the change form).

## 3. Tests

- [x] 3.1 Update/extend `artworks/tests.py` changelist assertions to the new exact column order for `ArtistAdmin` and `ArtworkAdmin`.
- [x] 3.2 Run `venv/bin/python manage.py test artworks --verbosity=2` and confirm green.
