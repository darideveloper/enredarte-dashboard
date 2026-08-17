from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from artworks.models import Artwork, ArtworkStatus
from artworks.serializers import ArtistRefSerializer, ArtworkSerializer, RefSerializer

TAXONOMY_FIELDS = ("disciplines", "techniques", "themes", "formats", "scales")


class CatalogAPIView(APIView):
    """Authenticated, unpaginated snapshot of the buyable catalogue for the SSG build."""

    pagination_class = None

    def get(self, request):
        artworks = list(
            Artwork.objects.filter(is_active=True, status=ArtworkStatus.AVAILABLE)
            .order_by("sort_order", "id")
            .select_related("artist", "artist__location")
            .prefetch_related(
                "disciplines__translations",
                "techniques__translations",
                "themes__translations",
                "formats__translations",
                "scales__translations",
                "translations",
                "images",
                "artist__location__translations",
            )
        )

        artists = {}
        for artwork in artworks:
            artists[artwork.artist_id] = artwork.artist

        locations = {}
        for artist in artists.values():
            if artist.location_id:
                locations[artist.location_id] = artist.location

        taxonomies = {name: {} for name in TAXONOMY_FIELDS}
        for artwork in artworks:
            for name in TAXONOMY_FIELDS:
                for item in getattr(artwork, name).all():
                    taxonomies[name][item.id] = item

        return Response(
            {
                "generated_at": timezone.now().isoformat().replace("+00:00", "Z"),
                "artists": ArtistRefSerializer(
                    sorted(artists.values(), key=lambda a: (a.sort_order, a.id)), many=True
                ).data,
                "taxonomies": {
                    name: RefSerializer(
                        sorted(items.values(), key=lambda o: (o.sort_order, o.id)), many=True
                    ).data
                    for name, items in taxonomies.items()
                },
                "locations": RefSerializer(
                    sorted(locations.values(), key=lambda l: (l.sort_order, l.id)), many=True
                ).data,
                "artworks": ArtworkSerializer(artworks, many=True).data,
            }
        )
