from rest_framework.permissions import AllowAny
from rest_framework.viewsets import ReadOnlyModelViewSet

from blog.models import Post
from blog.serializers import PostDetailSerializer, PostSummarySerializer


class PostViewSet(ReadOnlyModelViewSet):
    """Public read-only ViewSet for blog post summary listing and full detail."""

    permission_classes = [AllowAny]
    lookup_field = "slug"

    def get_queryset(self):
        return (
            Post.objects.filter(is_active=True)
            .order_by("-published_at", "sort_order", "-id")
            .prefetch_related("translations")
        )

    def get_serializer_class(self):
        if self.action == "retrieve":
            return PostDetailSerializer
        return PostSummarySerializer
