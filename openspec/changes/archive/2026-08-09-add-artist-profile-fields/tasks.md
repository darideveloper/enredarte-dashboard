## 1. Models

- [x] 1.1 Add `ArtistSocialLink` to `artworks/models.py`: `BaseModel` subclass with `artist` FK (`related_name="social_links"`), `platform` (`TextChoices`: Instagram, Facebook, X, TikTok, LinkedIn, YouTube, Behance, Other), `url` (`URLField`), and `Meta.ordering = ["sort_order"]`
- [x] 1.2 Override `ArtistSocialLink.save()` to auto-fill `slug` from `artist.slug` + platform (with uniqueness suffix) when blank, so inline-created links never violate the unique slug constraint
- [x] 1.3 Add `Location` (`BaseModel`, Spanish verbose_name "Ubicación") and `LocationTranslation` (`TranslationBase`, `name`, `unique_together` on `(location, language)`) to `artworks/models.py`
- [x] 1.4 Add `Artist.location` FK (`SET_NULL`, null, blank, `related_name="artists"`)
- [x] 1.5 Add `Artwork.is_highlighted` (`BooleanField`, default `False`) and `Artwork.views_count` (`PositiveIntegerField`, default `0`)
- [x] 1.6 Add derived `@property`s on `Artist`: `techniques`, `available_artworks`, `new_additions`, `highlighted_artworks`, `most_viewed`, `curations` (per `specs/artist-derived-fields/spec.md` and design decision 1)
- [x] 1.7 Generate migration `0003_*.py` via `makemigrations` (3 `CreateModel` + 3 `AddField`; no data step)

## 2. Fixtures

- [x] 2.1 Create `artworks/fixtures/artworks/Location.json` (4 rows, stable PKs 1–4) + `LocationTranslation.json` (8 es/en rows) per the manifest in `specs/artist-location/spec.md`
- [x] 2.2 Update `artworks/fixtures/artworks/seed/Artist.json` to reference location PKs on the seed artists
- [x] 2.3 Create `artworks/fixtures/artworks/seed/ArtistSocialLink.json` (2–3 demo links per seed artist, referencing seed artist PKs)
- [x] 2.4 Confirm `base_loaddata` loads Locations and `seed_loaddata` loads the updated artists + social links without integrity errors

## 3. Admin

- [x] 3.1 Add `ArtistSocialLinkInline` (`TabularInline`, fields `platform`/`url`, `ordering_field="sort_order"`, `hide_ordering_field=True`) and include it in `ArtistAdmin.inlines`
- [x] 3.2 Add `LocationTranslationInline` and `LocationAdmin` (mirror taxonomy admins: es-pref `display_name`, slug/sort_order init, Spanish labels) and register it
- [x] 3.3 Add `location` field to `ArtistAdmin` fieldsets; add changelist `list_display` count columns (artworks, available, techniques, highlighted, galleries) and a readonly "Resumen" fieldset on the change form rendering the six derived blocks in detail, all via `display_*` methods over the model properties
- [x] 3.4 Update `ArtworkAdmin`: `is_highlighted` + `views_count` in the form fieldsets, changelist columns, and `is_highlighted` list filter

## 4. Tests

- [x] 4.1 Add model tests: `ArtistSocialLink` (create, platforms, auto-slug uniqueness), `Location` + translation, `Artist.location`
- [x] 4.2 Add `Artwork` tests for `is_highlighted` default/flag and `views_count` default/values
- [x] 4.3 Add `Artist` derived-property tests: techniques distinct, available_artworks filtering, new_additions ordering, highlighted filtering, most_viewed ordering, curations distinct galleries (the `techniques` test requires `Technique` rows — run `call_command("base_loaddata")` in `setUp` or create the taxonomy rows directly)
- [x] 4.4 Add admin tests: Artist changelist count columns + "Resumen" fieldset render, social links inline present, Location admin registered, Artwork discovery fields visible/filterable
- [x] 4.5 Ensure `makemigrations --check` and `manage.py test` pass

## 5. Verification

- [x] 5.1 Run `python manage.py makemigrations --check` + `migrate` (fresh DB)
- [x] 5.2 Run `python manage.py base_loaddata` and confirm the 4 locations
- [x] 5.3 Run `python manage.py seed_loaddata` and confirm seed artists have locations and social links
- [x] 5.4 Open admin: Artist form shows location + social links inline + "Resumen" fieldset with counts; Artwork form/changelist show `is_highlighted` and `views_count`
