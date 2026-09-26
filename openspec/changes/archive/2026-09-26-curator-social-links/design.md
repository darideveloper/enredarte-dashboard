## Context

See `proposal.md` for motivation. Currently, `ArtistSocialLink` exists in `artworks/models.py` with 8 predefined platform choices, an auto-slugifying `save()` method, and an inline on `ArtistAdmin`. `ArtCurator` inherits from `Person` alongside `Artist`, but has only `ArtCuratorTranslationInline` on `ArtCuratorAdmin` and no social links. In the REST API, `ArtistSerializer` inlines active `social_links` while `ArtCuratorSerializer` has no `social_links` field.

## Goals / Non-Goals

**Goals:**
- Provide an `ArtCuratorSocialLink` model with full schema and behavioral symmetry to `ArtistSocialLink`.
- Extract common logic (platform enum, URL field, auto-slugification, content-based string display) into an abstract `BaseSocialLink` model without altering the database schema or table name of `ArtistSocialLink`.
- Expose `ArtCuratorSocialLinkInline` (`TabularInline`) in `ArtCuratorAdmin` below the translation inlines.
- Include active social links in `ArtCuratorSerializer` and optimize `ArtCuratorViewSet` with active prefetching.
- Ship realistic demo seed data for curators in `01b_ArtCuratorSocialLink.json`.
- Maintain complete Django test coverage across models, admin inlines, and API endpoints.

**Non-Goals:**
- Modifying the underlying database table name or columns of `ArtistSocialLink`.
- Adding new social network platforms or altering existing platform enum keys/values.
- Introducing drag-and-drop or manual `sort_order` ordering (per project convention established in `openspec/specs/artist-social-links`).

## Decisions

### Decision 1: Shared abstract model (`BaseSocialLink`) vs. code duplication
- **Choice**: Extract `BaseSocialLink(BaseModel)` with `abstract = True` in `artworks/models.py`. Both `ArtistSocialLink` and `ArtCuratorSocialLink` inherit from it.
- **Rationale**: Keeps the platform choices (`Platform.choices`), URL validation, slug auto-generation (`{parent.slug}-{platform}`), and `__str__` format (`"{platform} — {parent}"`) DRY. Because `BaseSocialLink` is abstract, Django creates no database table for it; `ArtistSocialLink` continues mapping to the existing `artworks_artistsociallink` table without requiring any schema changes or table alters.
- **Alternatives considered**:
  - *Separate independent models*: Duplicate all 30 lines of choice definitions, slugification, and string methods. Rejected due to drift risk if platforms change.
  - *GenericForeignKey (single SocialLink table)*: Use Django content types. Rejected because it complicates database integrity, degrades query optimization, and creates UI friction in Unfold tabular inlines.

### Decision 2: Admin inline presentation (`ArtCuratorSocialLinkInline`)
- **Choice**: Register `ArtCuratorSocialLinkInline` as a `TabularInline` with fields `["platform", "url"]`, `verbose_name = "Red social"`, `verbose_name_plural = "Redes sociales"`, and `extra = 0`.
- **Rationale**: Matches `ArtistSocialLinkInline` exactly. Administrators can add, edit, or delete multiple curator links directly on the curator edit page without extra clicks or navigation.

### Decision 3: API serialization and query optimization
- **Choice**: Add `social_links = ArtCuratorSocialLinkSerializer(many=True, read_only=True)` to `ArtCuratorSerializer`, outputting `[{"id": ..., "platform": ..., "url": ...}]`. In `ArtCuratorViewSet.get_queryset()`, prefetch with `Prefetch("social_links", queryset=ArtCuratorSocialLink.objects.filter(is_active=True))`.
- **Rationale**: Eliminates N+1 queries, satisfies `nested-active-filtering`, and provides exact parity with `ArtistSerializer`.

### Decision 4: Fixture ordering and naming
- **Choice**: Name the seed fixture `artworks/fixtures/artworks/seed/01b_ArtCuratorSocialLink.json`.
- **Rationale**: `seed_loaddata` loads fixtures alphabetically. `00_ArtCurator.json` creates curators (PKs 1 and 2), followed by `01_ArtCuratorTranslation.json`. `01b_ArtCuratorSocialLink.json` executes immediately after curator creation and before `02_Artist.json`, ensuring foreign keys resolve reliably.

## Risks / Trade-offs

- **[Risk] Unintended schema migration on `ArtistSocialLink` when refactoring to `BaseSocialLink`**  
  → *Mitigation*: Ensure `BaseSocialLink` sets `abstract = True` and fields on `ArtistSocialLink` retain identical types, max_lengths, and verbose_names so `makemigrations` detects only the creation of `ArtCuratorSocialLink`.
- **[Risk] Fixture loading failure during fresh bootstrap**  
  → *Mitigation*: Validate foreign key PK references against `00_ArtCurator.json` (PKs 1 and 2) and verify with `python manage.py seed_loaddata` during tests.
- **[Risk] Inactive links leaking through API endpoints**  
  → *Mitigation*: Enforce `is_active=True` filter via DRF `Prefetch` in `ArtCuratorViewSet` and verify with targeted test cases in `artworks/tests.py`.
