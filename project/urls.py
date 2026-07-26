import project.admin
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from rest_framework import routers

router = routers.DefaultRouter()

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", RedirectView.as_view(url="/admin/"), name="home-redirect-admin"),
    path("api/", include(router.urls)),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
