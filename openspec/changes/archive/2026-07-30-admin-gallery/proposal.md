# Proposal: Admin Gallery

## Description
This change registers the `Gallery` model into the Django Admin dashboard using `django-unfold`. It will provide an interface for curators to manage their galleries, including a drag-and-drop sortable inline for curating artworks within the gallery.

## Goal
To allow administrators to easily create and manage Galleries, including pre-populated Spanish/English fields for name and description, and the ability to curate artworks in a specific order.

## Value
This provides the essential management interface for physical or virtual gallery spaces and paves the way for the full Artwork admin implementation by allowing Artworks to be mapped to their exhibition spaces.

## Scope
- Register `Gallery` in `artworks/admin.py`.
- Create a translation inline for `GalleryTranslation` (`GalleryTranslationInline`).
- Create a sortable tabular inline for `ArtworkGallery` (`ArtworkGalleryInline`) to allow drag-and-drop artwork curation.
- Implement custom `display_name` logic in the list view that falls back to available translations.

## Non-goals
- Do not implement the `Artwork` admin in this change.
