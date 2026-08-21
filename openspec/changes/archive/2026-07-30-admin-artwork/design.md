## Context

`Artwork` is the core entity that references almost every other model in the `artworks` app (`Artist`, `Category`, `Medium`, `Surface`, `Gallery`, `ArtworkImage`, `ArtworkTranslation`). We need a clean, structured admin design that makes editing these interconnected models simple and intuitive.

## Goals

1. Register `Artwork` in `artworks/admin.py` with `ModelAdminUnfoldBase`.
2. Group form fields into logical fieldsets: Basic Info, Classification, Pricing & Status, and System Info.
3. Include inline editors for `ArtworkTranslation`, `ArtworkImage` (drag-and-drop sortable), and `ArtworkGallery`.
4. Render custom display methods for list view (primary image thumbnail, localized title, formatted price, status badge).

## Decisions

- **Decision 1: Use `TabularInline` for `ArtworkImage` with `ordering_field`**
  **Rationale**: Images need to be ordered sequentially for display on the public site. Setting `ordering_field = "sort_order"` gives admins a drag-and-drop UI to order images.

- **Decision 2: Image Preview in `ArtworkImageInline` and `list_display`**
  **Rationale**: Displaying small thumbnail previews in the inline rows and list view table makes visually managing artworks intuitive.

- **Decision 3: Grouped Fieldsets**
  **Rationale**: Grouping fields into 4 cards (Main Attributes, Taxonomies, Commercial & Status, System Info) avoids a single overwhelmingly long form.

- **Decision 4: `TranslationInlineFormSet` for `ArtworkTranslationInline`**
  **Rationale**: Ensures `es` and `en` language entries are pre-populated automatically on creation.

- **Decision 5: Custom `display_title` and `display_price`**
  **Rationale**: `display_title` will show Spanish with English fallback. `display_price` will show both MXN and USD formatted nicely.

## Risks / Trade-offs

- **Form Length**: With 3 inlines (`ArtworkTranslationInline`, `ArtworkImageInline`, `ArtworkGalleryInline`), the change form can be tall. Unfold handles tabs/sections well, and fieldsets will keep it organized.
