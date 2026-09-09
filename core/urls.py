from django.urls import path

from core.views import publish_changes_view

app_name = "core"

urlpatterns = [
    path("publish/", publish_changes_view, name="publish-changes"),
]
