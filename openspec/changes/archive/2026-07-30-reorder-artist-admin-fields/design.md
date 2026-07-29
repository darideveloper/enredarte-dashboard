## Context

The layout for `ArtistAdmin` currently defaults to the model field inheritance order, which places `slug` at the top. The `slug` field should intuitively follow the `name` field, as it is prepopulated from it.

## Goals / Non-Goals

**Goals:**
- Move `slug` below `name` in the UI.
- Use `fieldsets` for grouping logical information in the admin panel.

**Non-Goals:**
- No changes to the underlying `Artist` or `Person` data model.

## Decisions

- **Decision**: Define `fieldsets` in `ArtistAdmin`. 
  **Rationale**: This achieves both field reordering (to place `slug` immediately after `name` on the same row) and groups fields cleanly using Unfold's UI improvements.

## Risks / Trade-offs

- None, this is a standard configuration change in Django's admin.
