import logging

import stripe
from django import forms
from django.contrib import admin, messages
from django.db import transaction
from django.db.models import Exists, OuterRef
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)

from artworks.models import Artist
from project.admin_base import ModelAdminUnfoldBase
from solo.admin import SingletonModelAdmin
from subscriptions.admin_helpers import subscription_badge
from subscriptions.models import ArtistSubscription, BillingPlan, BillingPlanPriceHistory, StripeEvent
from subscriptions.services import stripe_client
from subscriptions.services.stripe_compat import sget


class BillingPlanForm(forms.ModelForm):
    class Meta:
        model = BillingPlan
        fields = [
            "name",
            "amount",
            "currency",
            "interval",
            "grace_period_days",
            "is_active_for_new_signups",
        ]

    def clean(self):
        cleaned = super().clean()
        amount = cleaned.get("amount")
        currency = cleaned.get("currency")
        interval = cleaned.get("interval")
        if amount is not None and amount <= 0:
            raise forms.ValidationError(_("El monto debe ser mayor que 0."))
        if currency is not None and currency not in {"MXN", "USD"}:
            raise forms.ValidationError(_("Moneda no válida. Use MXN o USD."))
        if interval is not None and interval != "month":
            raise forms.ValidationError(_("Intervalo no válido. Solo se permite mensual."))
        return cleaned


class BillingPlanPriceHistoryInline(admin.TabularInline):
    model = BillingPlanPriceHistory
    extra = 0
    can_delete = False
    ordering = ("-changed_at",)
    readonly_fields = [
        "billing_plan",
        "old_stripe_price_id",
        "new_stripe_price_id",
        "amount",
        "currency",
        "interval",
        "old_price_archived",
        "changed_at",
        "changed_by",
    ]

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(BillingPlan)
class BillingPlanAdmin(SingletonModelAdmin, ModelAdminUnfoldBase):
    """django-solo singleton edited in the Unfold admin.

    Inherits from `SingletonModelAdmin` so the changelist is skipped and the
    single edit page is shown directly under "Suscripciones / Plan de
    suscripción". `ModelAdminUnfoldBase` provides the Unfold theme.
    """

    form = BillingPlanForm
    sidebar_icon = "subscriptions"
    readonly_fields = [
        "stripe_product_id",
        "stripe_price_id",
        "last_synced_stripe_at",
        "display_stripe_live",
    ]
    fieldsets = (
        (None, {
            "fields": (
                "name",
                "amount",
                "currency",
                "interval",
                "grace_period_days",
                "is_active_for_new_signups",
            )
        }),
        (_("Stripe"), {
            "fields": (
                "stripe_product_id",
                "stripe_price_id",
                "last_synced_stripe_at",
                "display_stripe_live",
            )
        }),
    )
    inlines = [BillingPlanPriceHistoryInline]

    @admin.display(description=_("Confirmado por Stripe"))
    def display_stripe_live(self, obj):
        # Thread-safe: prefer request._stripe_live_summary if available (set in change_view)
        # Fallback to self for backwards compat / when request not present.
        req = getattr(self, "_current_request", None)
        if req is not None and hasattr(req, "_stripe_live_summary"):
            return getattr(req, "_stripe_live_summary", "(sin confirmar)")
        return getattr(self, "_stripe_live_summary", "(sin confirmar)")

    def change_view(self, request, object_id, form_url="", extra_context=None):
        extra_context = extra_context or {}
        plan = self.get_object(request, object_id)
        if plan and plan.stripe_price_id:
            try:
                price = stripe_client.retrieve_price(plan.stripe_price_id)
                unit_amount = sget(price, "unit_amount", 0) or 0
                currency = sget(price, "currency", "") or ""
                recurring = sget(price, "recurring", None)
                interval = sget(recurring, "interval", "") or ""
                pid = sget(price, "id", plan.stripe_price_id)
                extra_context["stripe_live_summary"] = (
                    f"Confirmado por Stripe: {unit_amount / 100:.2f} {currency.upper()} / {interval} ({pid})"
                )
            except stripe.error.StripeError as e:
                logger.warning("BillingPlan preview StripeError price=%s: %s", plan.stripe_price_id, e)
                extra_context["stripe_live_summary"] = "(no se pudo confirmar)"
            except Exception as e:
                logger.warning("BillingPlan preview failed price=%s: %s", plan.stripe_price_id, e)
                extra_context["stripe_live_summary"] = "(no se pudo confirmar)"
        else:
            extra_context["stripe_live_summary"] = "(sin confirmar)"
        # Thread-safe storage on request, keep self as fallback for display method
        request._stripe_live_summary = extra_context.get("stripe_live_summary", "(sin confirmar)")
        self._stripe_live_summary = request._stripe_live_summary
        self._current_request = request
        return super().change_view(request, object_id, form_url, extra_context)

    @transaction.atomic
    def save_model(self, request, obj, form, change):
        from subscriptions.services import plan_sync

        try:
            plan_sync.ensure_stripe_price(obj, user=request.user)
        except stripe.error.StripeError as e:
            messages.error(request, f"Stripe no respondió: {e}. Nada se guardó.")
            raise
        # Save editable fields (inside same atomic as ensure_stripe_price's
        # history+stripe fields would be, but ensure uses its own atomic.
        # Wrapping here guarantees no partial commit if super fails.)
        super().save_model(request, obj, form, change)


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