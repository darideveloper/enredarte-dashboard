## Context

The `Gallery` model encapsulates its translatable fields (`name` and `description`) inside `GalleryTranslation`. It also serves as the parent container for artworks through the `ArtworkGallery` mapping model. We want to provide a seamless curation experience by allowing admins to reorder artworks within a gallery via drag-and-drop.

## Goals

1. Register `Gallery` in `artworks/admin.py`.
2. Provide pre-populated bilingual translation fields for the gallery's name and description.
3. Provide a drag-and-drop sortable interface for adding and organizing artworks.

## Decisions

- **Decision 1: Leverage `TranslationInlineFormSet`**
  **Rationale**: We will reuse our `TranslationInlineFormSet` for `GalleryTranslationInline` to ensure `es` and `en` fields are pre-populated, maintaining consistency with all other models.

- **Decision 2: Manual `slug` entry**
  **Rationale**: Like the taxonomy models, the `slug` is on the parent model while `name` is translated. `prepopulated_fields` cannot span relationships, so the slug must be manually entered.

- **Decision 3: Use Unfold's built-in `ordering_field` for drag-and-drop**
  **Rationale**: Django Unfold supports sortable inlines natively. By creating an `ArtworkGalleryInline` inheriting from `unfold.admin.TabularInline` and setting `ordering_field = "sort_order"`, we automatically get a drag-and-drop interface for curating artworks within the gallery. We will set `hide_ordering_field = True` to keep the UI clean.

- **Decision 4: Custom `display_name`**
  **Rationale**: We will add a method that queries the `es` translation first, falling back to the first available if `es` is missing, to display the name in the changelist table.

- **Decision 5: Appropriate Icon**
  **Rationale**: We will use the `storefront` Material Symbol icon for the Gallery admin.

## Risks / Trade-offs

- **Manual Slug Entry**: Users might make typos in the slug. Out of scope for this change.
- **Empty Artworks**: At the moment, the `Artwork` model is not implemented in the admin, so we won't be able to easily create Artworks *from* the Gallery admin, but we can establish the relationship structure now.
