from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from core.models import StripeEvent
from project.admin_base import ModelAdminUnfoldBase


@admin.register(StripeEvent)
class StripeEventAdmin(ModelAdminUnfoldBase):
    sidebar_icon = "receipt_long"
    list_display = [
        "event_type",
        "display_event_id",
        "received_at",
        "processed_at",
        "display_error",
    ]
    list_filter = ["event_type", "received_at"]
    search_fields = ["event_id", "event_type"]
    readonly_fields = [
        "event_id",
        "event_type",
        "received_at",
        "processed_at",
        "payload",
        "error",
    ]
    date_hierarchy = "received_at"
    list_per_page = 50

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.display(description=_("ID del evento"))
    def display_event_id(self, obj):
        return obj.event_id[:30]

    @admin.display(description=_("Error"))
    def display_error(self, obj):
        return obj.error or "-"
