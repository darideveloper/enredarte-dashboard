## Why

`sort_order` is inherited by 11 models through `BaseModel` but is only genuinely used by two models — `ArtworkGallery` and `ArtworkImage` — that manage ordered lists. Everywhere else it is dead weight: an unused admin field, an unused DB column, an unused API field, and unused fixture values that add noise, confusion, and maintenance burden for no behavior.

## What Changes

- **BREAKING**: Remove the `sort_order` field from the abstract `BaseModel` in `core/models.py`.
- **BREAKING**: Drop the `sort_order` column from the 11 affected models (`Artist`, `ArtCurator`, `ArtistSocialLink`, `Location`, `Gallery`, `Discipline`, `Technique`, `Theme`, `Format`, `Scale`, `Artwork`) via a new migration.
- Keep `sort_order` **only** on `ArtworkGallery` and `ArtworkImage`, including their `Meta.ordering` and admin inline drag-and-drop ordering.
- Remove `sort_order` from the Django Admin: `fieldsets`, `list_display`, the auto-fill `get_changeform_initial_data` methods, and the `Max` aggregates that backed them.
- **BREAKING**: Remove `sort_order` from REST API response payloads for the affected entities; replace `order_by("sort_order")` queryset ordering with `order_by("-created_at")`.
- Remove `sort_order` from Bruno API collection examples, seed fixtures, tests, and the affected live openspec specs.
- Replace sort-based ordering in the `Artist.techniques`, `available_artworks`, and `highlighted_artworks` properties with `-created_at`.

## Capabilities

### New Capabilities

None — this is a simplification/removal refactor.

### Modified Capabilities

- `artworks-rest-api`: Response payloads drop `sort_order` for artists, art-curators, locations, galleries, taxonomies, and artworks; list ordering becomes `-created_at`. `sort_order` remains on `images` and `gallery_links`/`artwork_links`.
- `artwork-taxonomies`: Taxonomy models no longer inherit `sort_order` from `BaseModel`.
- `artist-location`: `Location` no longer inherits `sort_order` from `BaseModel`.
- `artist-social-links`: `ArtistSocialLink` loses `sort_order`, its `Meta.ordering`, and its sortable inline behavior.
- `artist-admin`: `ArtistSocialLinkInline` is no longer sortable via `sort_order`.
- `art-curator-admin`: The auto-fill `sort_order` behavior on the ArtCurator add form is removed.
- `admin-spanish-labels`: `sort_order` is dropped from the list of inherited `BaseModel` fields; it remains a Spanish-labeled concrete field on `ArtworkGallery`/`ArtworkImage`.
- `artworks-api-bruno`: Taxonomy resource examples drop `sort_order`.

## Impact

- **Code**: `core/models.py`, `artworks/models.py`, `artworks/admin.py`, `artworks/serializers.py`, `artworks/views.py`, `artworks/tests.py`.
- **Database**: New migration removing the `sort_order` column from 11 tables.
- **API**: Response contract change (field removed) — frontend consumers must stop reading `sort_order` on those entities.
- **Data/fixtures**: 11 fixture files must drop `sort_order` or `loaddata` (used by `start.sh`, Dockerfile, and tests) will fail.
- **Tooling/docs**: Bruno collection (20 request files) and 8 live openspec specs updated.