## Context

The `ArtCurator` model needs an admin interface. It is similar to `Artist` but lacks birth/death years. We want an inline translation form that behaves just like `ArtistTranslationInline`, pre-populating available languages. Additionally, we want to auto-fill the `sort_order` for curators.

## Goals / Non-Goals

**Goals:**
- Provide a clean Unfold admin interface for `ArtCurator`.
- Pre-populate `es` and `en` translation languages on creation, suppressing extras when full.
- Auto-fill `sort_order` with `max(sort_order) + 1` for new curators.
- Keep code DRY without touching models.

**Non-Goals:**
- Do not move `sort_order` auto-fill logic into `ModelAdminUnfoldBase` globally yet.

## Decisions

- **Decision 1: Rename `ArtistTranslationFormSet` to `TranslationInlineFormSet`**
  **Rationale**: The logic for pre-populating translation forms is identical. Renaming the class allows both `ArtistTranslationInline` and the new `ArtCuratorTranslationInline` to share the same code cleanly.

- **Decision 2: Replicate layout structure from `ArtistAdmin`**
  **Rationale**: Consistency. `ArtCuratorAdmin` will use fieldsets: `Personal Info` (name, slug), `Contact & Media` (email, website, photo), and `System Status` (is_active, sort_order).

- **Decision 3: Duplicate `sort_order` auto-fill in `ArtCuratorAdmin`**
  **Rationale**: Per requirements, we will scope this to the model specifically for now. We will just duplicate the `get_changeform_initial_data` method into `ArtCuratorAdmin`.

## Risks / Trade-offs

- **Code Duplication**: Duplicating `get_changeform_initial_data` creates slightly wet code, but it complies directly with the requested scope. We can refactor it to a mixin or base class later if needed.
