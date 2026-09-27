## Why

Enredarte needs to track the agreed commercial split between artists and the platform for artwork sales. Currently, the `Artist` model has no internal field for recording the artist's commission rate, and administrators have no place in Django Admin to view or manage this commercial percentage when viewing artists, inspecting individual artworks, or auditing completed artwork sales.

## What Changes

- **Artist Model**: Add an internal `commission` field (`PositiveSmallIntegerField`, validated between 0 and 100, default 0) to `Artist` representing the percentage of artwork sales that belongs to the artist (the remaining percentage belongs to Enredarte).
- **Artist Admin Changelist**: Add the artist commission column (`display_commission`) to `ArtistAdmin.list_display`, positioned next to the first columns (between Name and Email), displaying formatted values such as `25%`.
- **Artist Admin Change Form**: Add `commission` to `ArtistAdmin.fieldsets` under a dedicated "Acuerdo comercial" section.
- **Artwork Admin Detail View**: Add a read-only `display_artist_commission` field to `ArtworkAdmin.fieldsets` and `readonly_fields` so operators see the artist's commission percentage when viewing or editing an artwork.
- **Artwork Order Admin Detail View**: Add a read-only `display_artist_commission` field to `ArtworkOrderAdmin.fieldsets` and `readonly_fields` under the "Pedido" section so operators see the artist's commission percentage when inspecting sales orders.
- **Database Migration**: Generate and apply a migration for the new `commission` field on `Artist`.
- **Admin & Model Tests**: Add test cases covering model validation (0-100 range), artist changelist display, and read-only commission rendering in artwork and sale admin views.
- **Internal Only**: Keep the field strictly internal to the admin; public REST APIs and serializers remain untouched.

## Capabilities

### New Capabilities
- `artist-commission`: Defines the internal artist commission field on the `Artist` model, including percentage constraints (0-100), default value, Spanish admin verbose naming, and help text.

### Modified Capabilities
- `artist-admin`: Adds the commission percentage column next to the first columns in `ArtistAdmin.list_display` and exposes the editable `commission` field in `ArtistAdmin.fieldsets`.
- `artwork-admin`: Adds a read-only artist commission percentage display to `ArtworkAdmin` detail view.
- `artwork-sales`: Adds a read-only artist commission percentage display to `ArtworkOrderAdmin` (sale detail view).

## Impact

- **Models**: `artworks/models.py` (`Artist` model gains `commission`).
- **Migrations**: New migration in `artworks/migrations/` adding `commission` column with `default=0`.
- **Admin**: `artworks/admin.py` (`ArtistAdmin`, `ArtworkAdmin`, `ArtworkOrderAdmin`).
- **APIs / Serializers**: None (strictly internal admin feature; public endpoints are unaffected).
- **Dependencies**: None.
