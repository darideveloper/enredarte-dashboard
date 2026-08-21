# Proposal: Admin Artwork

## Description
This change registers the `Artwork` model into the Django Admin dashboard using `django-unfold`. It provides a comprehensive, multi-section form to manage artwork details, translatable titles/descriptions, foreign key relations (Artist, Category, Medium, Surface), image uploads with drag-and-drop ordering, and gallery assignments.

## Goal
To allow administrators to easily create and manage Artworks, including bilingual titles/descriptions, primary image designation, gallery links, and pricing in both MXN and USD.

## Value
Artwork is the primary domain entity of the dashboard. Having a fully featured admin interface allows curators to manage their catalog, prices, status, and high-resolution image galleries effortlessly.

## Scope
- Register `Artwork` in `artworks/admin.py`.
- Create `ArtworkTranslationInline` (StackedInline) for translatable title and description fields (es/en).
- Create `ArtworkImageInline` (TabularInline) with drag-and-drop `sort_order` reordering and image preview thumbnails.
- Support foreign key relationships to `Artist`, `Category`, `Medium`, `Surface`, and `Gallery` (`ArtworkGalleryInline`).
- Implement list view with thumbnail previews, localized titles, price formatting, and status badges.

## Non-goals
- Bulk image uploading (standard inline uploads are sufficient for this version).
