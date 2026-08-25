import project.admin
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

from subscriptions import webhooks

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", RedirectView.as_view(url="/admin/"), name="home-redirect-admin"),
    path("apis/artworks/", include("artworks.urls")),
    path("api/blog/", include("blog.urls")),
    path("subscriptions/", include(("subscriptions.urls", "subscriptions"), namespace="subscriptions")),
    path("webhooks/stripe/", webhooks.stripe_webhook),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)