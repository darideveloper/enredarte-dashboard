from django.contrib import admin
from django.db.models import Exists, OuterRef
from django.utils.translation import gettext_lazy as _

from artworks.models import Artist
from project.admin_base import ModelAdminUnfoldBase
from solo.admin import SingletonModelAdmin
from subscriptions.admin_helpers import subscription_badge
from subscriptions.models import ArtistSubscription, BillingPlan, StripeEvent


@admin.register(BillingPlan)
class BillingPlanAdmin(SingletonModelAdmin, ModelAdminUnfoldBase):
    """django-solo singleton edited in the Unfold admin.

    Inherits from `SingletonModelAdmin` so the changelist is skipped and the
    single edit page is shown directly under "Suscripciones / Plan de
    suscripción". `ModelAdminUnfoldBase` provides the Unfold theme.
    """

    sidebar_icon = "subscriptions"
    fieldsets = (
        (None, {
            "fields": (
                "name",
                "stripe_price_id",
                "currency",
                "grace_period_days",
                "is_active_for_new_signups",
            )
        }),
    )


class ArtistIsActiveFilter(admin.SimpleListFilter):
    title = _("Artista activo")
    parameter_name = "artist_is_active"

    def lookups(self, request, model_admin):
        return (
            ("1", _("Activo")),
            ("0", _("Inactivo")),
        )

    def queryset(self, request, queryset):
        active = Artist.objects.filter(
            pk=OuterRef("artist_id"), is_active=True
        )
        if self.value() == "1":
            return queryset.filter(Exists(active))
        if self.value() == "0":
            return queryset.filter(~Exists(active))
        return queryset


@admin.register(ArtistSubscription)
class ArtistSubscriptionAdmin(ModelAdminUnfoldBase):
    sidebar_icon = "credit_card"
    list_display = [
        "artist",
        "display_status",
        "created_at",
        "current_period_end",
        "last_synced_at",
        "cancel_at_period_end",
    ]
    list_filter = [
        "status",
        ArtistIsActiveFilter,
    ]
    search_fields = [
        "artist__name",
        "artist__email",
        "stripe_subscription_id",
        "stripe_customer_id",
    ]
    readonly_fields = [
        "artist",
        "status",
        "stripe_customer_id",
        "stripe_subscription_id",
        "customer_email",
        "current_period_end",
        "cancel_at_period_end",
        "signup_url",
        "signup_url_expires_at",
        "last_synced_at",
        "raw_state",
        "created_at",
        "updated_at",
    ]
    list_per_page = 50

    @admin.display(description=_("Estado"))
    def display_status(self, obj):
        return subscription_badge(obj)


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