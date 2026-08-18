## 1. Serializer changes

- [x] 1.1 Add `ActiveRefField(RefSerializer)` in `artworks/serializers.py` whose `to_representation` returns `None` when the object is `None` or `is_active=False`, otherwise the `{id, slug}` ref.
- [x] 1.2 Swap `ArtistSerializer.location` to `ActiveRefField(allow_null=True)`.
- [x] 1.3 Swap `GallerySerializer.curator` to `ActiveRefField(allow_null=True)`.

## 2. Viewset querysets

- [x] 2.1 Replace `ArtistViewSet.queryset` with `get_queryset()`: `Artist.objects.filter(is_active=True).select_related("location")` + `Prefetch("social_links", queryset=ArtistSocialLink.objects.filter(is_active=True))` + `translations`, `.order_by("sort_order")`.
- [x] 2.2 Replace `GalleryViewSet.queryset` with `get_queryset()`: `Gallery.objects.filter(is_active=True).select_related("curator")` + `Prefetch("artwork_links", queryset=ArtworkGallery.objects.filter(is_active=True, artwork__is_active=True).select_related("artwork").order_by("sort_order"))` + `translations`, `.order_by("sort_order")`.
- [x] 2.3 Replace `ArtworkViewSet.queryset` with `get_queryset()`: filter `is_active=True` and `artist__is_active=True`, `select_related("artist")`, plus filtered `Prefetch` for the five taxonomy M2Ms, `images`, and `gallery_links` (link `is_active=True, gallery__is_active=True`, `select_related("gallery")`), and `translations`, `.order_by("sort_order")`.
- [x] 2.4 Add the `Prefetch` import in `artworks/views.py`.

## 3. Tests

- [x] 3.1 Add test: inactive `ArtistSocialLink` excluded from artist response.
- [x] 3.2 Add test: artist with inactive `location` returns `location: null`.
- [x] 3.3 Add test: gallery with inactive `curator` returns `curator: null`.
- [x] 3.4 Add test: gallery `artwork_links` with inactive artwork (and inactive link row) excluded.
- [x] 3.5 Add test: artwork `gallery_links` with inactive gallery excluded.
- [x] 3.6 Add test: artwork M2M ref array excludes an inactive taxonomy term.
- [x] 3.7 Add test: artwork `images` exclude inactive `ArtworkImage` rows.
- [x] 3.8 Add test: artwork whose artist is inactive is absent from list and 404s on detail.
- [x] 3.9 Run `python manage.py test artworks` and confirm the full suite passes.