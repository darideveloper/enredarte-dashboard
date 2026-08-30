"""URLs for the subscriptions app."""

from django.urls import path

from subscriptions import views

urlpatterns = [
    path("success/", views.success, name="success"),
    path("cancel/", views.cancel, name="cancel"),
    path("portal-return/", views.portal_return, name="portal-return"),
]
