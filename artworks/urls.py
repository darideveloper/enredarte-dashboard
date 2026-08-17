from rest_framework import routers

from artworks.views import (
    ArtCuratorViewSet,
    ArtistViewSet,
    ArtworkViewSet,
    DisciplineViewSet,
    FormatViewSet,
    GalleryViewSet,
    LocationViewSet,
    ScaleViewSet,
    TechniqueViewSet,
    ThemeViewSet,
)

router = routers.DefaultRouter()
router.register("artists", ArtistViewSet, basename="artist")
router.register("art-curators", ArtCuratorViewSet, basename="art-curator")
router.register("locations", LocationViewSet, basename="location")
router.register("galleries", GalleryViewSet, basename="gallery")
router.register("disciplines", DisciplineViewSet, basename="discipline")
router.register("techniques", TechniqueViewSet, basename="technique")
router.register("themes", ThemeViewSet, basename="theme")
router.register("formats", FormatViewSet, basename="format")
router.register("scales", ScaleViewSet, basename="scale")
router.register("artworks", ArtworkViewSet, basename="artwork")

urlpatterns = router.urls
