from rest_framework import viewsets

from artworks.models import (
    ArtCurator,
    Artist,
    Artwork,
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
    queryset = Artist.objects.filter(is_active=True).prefetch_related(
        "location", "translations", "social_links"
    ).order_by("sort_order")
    serializer_class = ArtistSerializer


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
    queryset = Gallery.objects.filter(is_active=True).prefetch_related(
        "curator", "translations", "artwork_links__artwork"
    ).order_by("sort_order")
    serializer_class = GallerySerializer


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
    queryset = Artwork.objects.filter(is_active=True).prefetch_related(
        "artist", "disciplines", "techniques", "themes", "formats", "scales",
        "translations", "images", "gallery_links__gallery",
    ).order_by("sort_order")
    serializer_class = ArtworkSerializer
