"""URLs for the subscriptions app.

Implementation choice (task 5.2): plain Django function-based views. Each
admin endpoint is wrapped with `admin.site.admin_view`, which provides the
staff-only gate (redirect to admin login for anonymous users, HTTP 403 for
non-staff). The Stripe webhook is mounted directly in `project/urls.py` at
`/webhooks/stripe/`, outside the admin.
"""

from django.contrib import admin
from django.urls import path

from subscriptions import views

urlpatterns = [
    path(
        "admin/artists/<int:artist_id>/generate-link/",
        admin.site.admin_view(views.generate_link),
        name="generate-link",
    ),
    path(
        "admin/artists/<int:artist_id>/regenerate-link/",
        admin.site.admin_view(views.regenerate_link),
        name="regenerate-link",
    ),
    path(
        "admin/artists/<int:artist_id>/open-portal/",
        admin.site.admin_view(views.open_portal),
        name="open-portal",
    ),
    path(
        "admin/artists/<int:artist_id>/sync-from-stripe/",
        admin.site.admin_view(views.sync_from_stripe),
        name="sync-from-stripe",
    ),
    path("success/", views.success, name="success"),
    path("cancel/", views.cancel, name="cancel"),
    path("portal-return/", views.portal_return, name="portal-return"),
]