## Context

The `Artist` and `ArtistTranslation` models in `artworks/models.py` are finalized and MUST NOT be altered. All admin customizations, inline models, and Spanish UI headers must be declared strictly within `artworks/admin.py`.

## Goals / Non-Goals

**Goals:**
- Register `Artist` model in Django Admin via `artworks/admin.py` using `unfold.contrib.inlines.StackedInline` for `ArtistTranslation`.
- Ensure Spanish and English `ArtistTranslation` rows are manageable directly within the same page as the `Artist` model in the admin.
- Localize all admin headers, inline titles, search placeholders, list table headers, and status display labels into Spanish.
- Use `ModelAdminUnfoldBase` to maintain design consistency with `django-unfold` theme.

**Non-Goals:**
- Modifying `artworks/models.py` or creating database migrations.
- Registering other artwork models (Gallery, Category, Artwork) in this specific subtask (they will follow in separate changes).

## Decisions

### Decision 1: Use `StackedInline` for `ArtistTranslationInline`
- **Rationale**: `ArtistTranslation` contains a `bio` text field. Using `StackedInline` allows broad text areas for writing biographies in Spanish and English without horizontal cramping.
- **Alternatives Considered**: `TabularInline` was considered but rejected because multi-line bio text fields are squeezed in table cells.

### Decision 2: Zero Model Modifications for Localization
- **Rationale**: The user explicitly constrained that `artworks/models.py` is finalized. We override column titles and verbose headers inside `artworks/admin.py` using `@admin.display(description=...)` and inline `verbose_name` overrides.
- **Alternatives Considered**: Modifying `class Meta` in `models.py` was rejected due to strict project constraints.

### Decision 3: Unfold Admin Customization
- **Rationale**: Configure `sidebar_icon = "palette"`, `search_fields = ["name", "email", "slug", "translations__bio"]`, `list_filter = ["is_active"]`, and `prepopulated_fields = {"slug": ("name",)}`.

## Risks / Trade-offs

- [Risk] Duplicate translation entries if language unique constraint is violated. → Mitigation: `ArtistTranslation` model already has `unique_together = [("artist", "language")]`. We set `extra = 2` on the inline for `es` and `en`.
