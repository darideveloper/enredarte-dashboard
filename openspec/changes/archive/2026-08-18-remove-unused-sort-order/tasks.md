## 1. Models & Migration

- [x] 1.1 Remove `sort_order` field from `BaseModel` in `core/models.py` (drop `sort_order = models.IntegerField(...)`)
- [x] 1.2 Update the `TranslatableName` docstring in `core/models.py` to no longer list `sort_order` among the inherited fields
- [x] 1.3 In `artworks/models.py`, change `Artist.techniques` (line 23), `Artist.available_artworks` (line 30), and `Artist.highlighted_artworks` (line 40) from `.order_by("sort_order")` to `.order_by("-created_at")`
- [x] 1.4 In `artworks/models.py`, remove `Meta.ordering = ["sort_order"]` from `ArtistSocialLink` (line 82)
- [x] 1.5 Verify `ArtworkGallery` and `ArtworkImage` keep their local `sort_order` fields (lines 293, 313) and `ArtworkImage.Meta.ordering` (line 316) unchanged
- [x] 1.6 Generate the migration with `python manage.py makemigrations artworks` and confirm it contains 11 `RemoveField` operations (artist, artcurator, artistsociallink, location, gallery, discipline, technique, theme, format, scale, artwork) and nothing else

## 2. Django Admin

- [x] 2.1 In `artworks/admin.py`, remove `ordering_field = "sort_order"` and `hide_ordering_field = True` from `ArtistSocialLinkInline` (lines 97–98)
- [x] 2.2 `ArtistAdmin`: remove `sort_order` from the "Estado del sistema" fieldset (line 219) and from `list_display` (line 241); delete the `get_changeform_initial_data` method (lines 244–248)
- [x] 2.3 `ArtCuratorAdmin`: remove `sort_order` from fieldset (line 376) and `list_display` (line 383); delete `get_changeform_initial_data` (lines 386–390)
- [x] 2.4 `DisciplineAdmin`, `TechniqueAdmin`, `ThemeAdmin`, `FormatAdmin`, `ScaleAdmin`: remove `sort_order` from each fieldset (lines 416, 443, 470, 497, 524) and `list_display` (lines 419, 446, 473, 500, 527); delete each `get_changeform_initial_data` (lines 421–425, 448–452, 475–479, 502–506, 529–533)
- [x] 2.5 `LocationAdmin`: remove `sort_order` from fieldset (line 551) and `list_display` (line 554); delete `get_changeform_initial_data` (lines 556–560)
- [x] 2.6 `GalleryAdmin`: remove `sort_order` from "Información del sistema" fieldset (line 582) and `list_display` (line 585); delete `get_changeform_initial_data` (lines 587–591)
- [x] 2.7 `ArtworkAdmin`: remove `sort_order` from "Configuración del sistema" fieldset (line 665) and `list_display` (line 678); delete `get_changeform_initial_data` (lines 681–685)
- [x] 2.8 Remove `Max` from the `django.db.models` import (line 5)
- [x] 2.9 Verify `ArtworkGalleryInline` (line 147), `GalleryArtworkInline` (line 157), and `ArtworkImageInline` (line 607) still keep `ordering_field = "sort_order"`

## 3. REST API

- [x] 3.1 In `artworks/serializers.py`, remove `"sort_order"` from `ArtistSerializer` (line 79), `ArtCuratorSerializer` (line 98), `LocationSerializer` (line 115), `GallerySerializer` (line 132), `_TaxonomySerializer` (line 148), and `ArtworkSerializer` (line 197)
- [x] 3.2 Verify `sort_order` remains in `ArtworkImageSerializer` (line 48), `ArtworkGalleryLinkSerializer` (line 59), and `GalleryArtworkLinkSerializer` (line 67)
- [x] 3.3 In `artworks/views.py`, replace `.order_by("sort_order")` with `.order_by("-created_at")` in `ArtistViewSet` (line 32), `ArtCuratorViewSet` (line 39), `LocationViewSet` (line 46), `GalleryViewSet` (line 53), `_TaxonomyViewSet` (line 61), and `ArtworkViewSet` (line 93)

## 4. Tests

- [x] 4.1 Delete `test_artist_add_view_sort_order_initial_when_empty` and `test_artist_add_view_sort_order_initial_when_artists_exist` (lines 135–148)
- [x] 4.2 Delete `test_curator_add_view_sort_order_initial_when_empty` and `test_curator_add_view_sort_order_initial_when_curators_exist` (lines 187–200)
- [x] 4.3 Delete `TaxonomyAdminMixin.test_add_view_sort_order_initial` (lines 245–249)
- [x] 4.4 Delete `test_gallery_initial_sort_order` (lines 317–322) and `test_artwork_initial_sort_order` (lines 391–396)
- [x] 4.5 Remove the `sort_order=` kwargs from `Gallery.objects.create` (line 304), `Artwork.objects.create` (line 371), `Location.objects.create` (line 1515), `Artist.objects.create` (lines 1524, 1531), `Discipline.objects.create` (line 1534), and `Gallery.objects.create` (line 1624)
- [x] 4.6 Remove the `"sort_order"` key from the admin POST payloads in `TranslationInlineEnforcementTestCase` and `SlugBackfillMixinTestCase` (lines 1236, 1257, 1278, 1303, 1327, 1358, 1403)
- [x] 4.7 Verify `ArtworkImage` keeps `sort_order=1` in the `ArtworksAPITestCase.setUp` (line 1564) and add an assertion that an artwork/artist serialized response has no top-level `sort_order` key

## 5. Fixtures

- [x] 5.1 Remove `sort_order` from base catalog fixtures: `Discipline.json`, `Format.json`, `Location.json`, `Scale.json`, `Technique.json`, `Theme.json`
- [x] 5.2 Remove `sort_order` from seed fixtures: `00_ArtCurator.json`, `02_Artist.json`, `03_ArtistSocialLink.json`, `05_Artwork.json`, `06_Gallery.json`
- [x] 5.3 Keep `sort_order` in `seed/08_ArtworkGallery.json` and `seed/09_ArtworkImage.json`
- [x] 5.4 Verify every affected fixture file loads: run `python manage.py loaddata` over the edited fixture files (or `base_loaddata`) with no `DeserializationError`

## 6. Bruno Collections

- [x] 6.1 Remove the top-level `sort_order` from the response examples in all 20 `.bru` files under `bruno/collections/enredarte-dashboard-api/` (Artists, ArtCurators, Locations, Galleries, Disciplines, Techniques, Themes, Formats, Scales, Artworks — list + detail each)
- [x] 6.2 Keep the nested `sort_order` in `images`, `gallery_links`, and `artwork_links` examples (Artworks and Galleries files)

## 7. Verification

- [x] 7.1 Confirm no pending model changes: `python manage.py makemigrations --check --dry-run`
- [x] 7.2 Run the full test suite (`python manage.py test`) and confirm green
- [x] 7.3 Grep for any remaining `sort_order` reference outside `ArtworkGallery`/`ArtworkImage` in code, fixtures, and Bruno docs; confirm only intended occurrences remain (models, migration, this change's specs, and the two keep models)