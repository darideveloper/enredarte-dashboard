## Why

Curators (`ArtCurator`) currently manage biographical translations, contact information, and portrait photos, but lack the ability to store and present social network profiles (Instagram, LinkedIn, X, etc.). In contrast, artists (`Artist`) have full social media link management via `ArtistSocialLink` and an inline editor on the artist admin page. Adding symmetrical social link capabilities to curators allows administrators to manage curator social networks in one place directly from the curator edit form and enables the REST API to expose curator social links to client applications.

## What Changes

- Introduce a shared `BaseSocialLink` abstract model to encapsulate typed platform choices, URL storage, auto-slugification, and content-based string representations without duplicating code between artists and curators.
- Refactor `ArtistSocialLink` to inherit from `BaseSocialLink` without modifying its database table name, schema, or stored values.
- Introduce `ArtCuratorSocialLink` inheriting from `BaseSocialLink`, linking each social link to an `ArtCurator` via a foreign key with cascade deletion.
- Register `ArtCuratorSocialLinkInline` as a `TabularInline` on `ArtCuratorAdmin`, enabling administrators to add, edit, and remove social links directly within the curator change form.
- Expose `social_links` in `ArtCuratorSerializer` as an array of `{id, platform, url}`, mirroring the `ArtistSerializer` response format.
- Update `ArtCuratorViewSet` to prefetch active social links (`is_active=True`) to maintain query efficiency and adhere to nested active filtering.
- Ship demo curator social links in a seed fixture loaded via `seed_loaddata`.
- Update Bruno API request documentation for `ArtCurators/GET detail.bru`.

## Capabilities

### New Capabilities
- `curator-social-links`: Defines the `ArtCuratorSocialLink` model, shared `BaseSocialLink` abstract base, platform choices, auto-generated slugs (`{curator.slug}-{platform}`), and demo seed fixture.

### Modified Capabilities
- `art-curator-admin`: Adds `ArtCuratorSocialLinkInline` tabular inline editing to `ArtCuratorAdmin`.
- `artworks-rest-api`: Adds `social_links` serialization to `ArtCuratorSerializer` and active prefetching to `ArtCuratorViewSet`.
- `nested-active-filtering`: Extends nested active collection filtering to exclude inactive `ArtCuratorSocialLink` rows from curator API responses.

## Impact

- **Models**: New `ArtCuratorSocialLink` model and `BaseSocialLink` abstract model in `artworks/models.py`. New migration in `artworks/migrations/`.
- **Admin**: `ArtCuratorSocialLinkInline` added to `artworks/admin.py` in `ArtCuratorAdmin.inlines`.
- **API**: `ArtCuratorSerializer` adds `social_links` field in `artworks/serializers.py`; `ArtCuratorViewSet` in `artworks/views.py` adds prefetching.
- **Fixtures**: New seed fixture `01b_ArtCuratorSocialLink.json` in `artworks/fixtures/artworks/seed/`.
- **API Documentation**: `bruno/collections/enredarte-dashboard-api/ArtCurators/GET detail.bru` updated.
- **Tests**: New model tests, admin inline tests, and API tests in `artworks/tests.py`.
