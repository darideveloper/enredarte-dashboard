from django.db.models import Prefetch
from rest_framework import viewsets

from artworks.models import (
    ArtCurator,
    Artist,
    ArtistSocialLink,
    Artwork,
    ArtworkGallery,
    ArtworkImage,
    Discipline,
    Format,
    Gallery,
    Location,
    Scale,
    Technique,
    Theme,
)
from artworks.serializers import (
    ArtCuratorSerializer,
    ArtistSerializer,
    ArtworkSerializer,
    DisciplineSerializer,
    FormatSerializer,
    GallerySerializer,
    LocationSerializer,
    ScaleSerializer,
    TechniqueSerializer,
    ThemeSerializer,
)


class ArtistViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ArtistSerializer

    def get_queryset(self):
        return Artist.objects.filter(is_active=True).select_related("location").prefetch_related(
            Prefetch("social_links", queryset=ArtistSocialLink.objects.filter(is_active=True)),
            "translations",
        ).order_by("sort_order")


class ArtCuratorViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ArtCurator.objects.filter(is_active=True).prefetch_related(
        "translations"
    ).order_by("sort_order")
    serializer_class = ArtCuratorSerializer


class LocationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Location.objects.filter(is_active=True).prefetch_related(
        "translations"
    ).order_by("sort_order")
    serializer_class = LocationSerializer


class GalleryViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = GallerySerializer

    def get_queryset(self):
        return Gallery.objects.filter(is_active=True).select_related("curator").prefetch_related(
            Prefetch(
                "artwork_links",
                queryset=ArtworkGallery.objects.filter(
                    is_active=True, artwork__is_active=True
                ).select_related("artwork").order_by("sort_order"),
            ),
            "translations",
        ).order_by("sort_order")


class _TaxonomyViewSet(viewsets.ReadOnlyModelViewSet):
    def get_queryset(self):
        return self.model.objects.filter(is_active=True).prefetch_related(
            "translations"
        ).order_by("sort_order")


class DisciplineViewSet(_TaxonomyViewSet):
    model = Discipline
    serializer_class = DisciplineSerializer


class TechniqueViewSet(_TaxonomyViewSet):
    model = Technique
    serializer_class = TechniqueSerializer


class ThemeViewSet(_TaxonomyViewSet):
    model = Theme
    serializer_class = ThemeSerializer


class FormatViewSet(_TaxonomyViewSet):
    model = Format
    serializer_class = FormatSerializer


class ScaleViewSet(_TaxonomyViewSet):
    model = Scale
    serializer_class = ScaleSerializer


class ArtworkViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ArtworkSerializer

    def get_queryset(self):
        return Artwork.objects.filter(
            is_active=True, artist__is_active=True
        ).select_related("artist").prefetch_related(
            Prefetch("disciplines", queryset=Discipline.objects.filter(is_active=True)),
            Prefetch("techniques", queryset=Technique.objects.filter(is_active=True)),
            Prefetch("themes", queryset=Theme.objects.filter(is_active=True)),
            Prefetch("formats", queryset=Format.objects.filter(is_active=True)),
            Prefetch("scales", queryset=Scale.objects.filter(is_active=True)),
            Prefetch(
                "images",
                queryset=ArtworkImage.objects.filter(is_active=True).order_by("sort_order"),
            ),
            Prefetch(
                "gallery_links",
                queryset=ArtworkGallery.objects.filter(
                    is_active=True, gallery__is_active=True
                ).select_related("gallery").order_by("sort_order"),
            ),
            "translations",
        ).order_by("sort_order")
