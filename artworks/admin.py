import json
import logging

import stripe
from django import forms
from django.conf import settings
from django.contrib import admin, messages
from django.contrib.admin import RelatedOnlyFieldListFilter
from django.core.exceptions import ValidationError
from django.db.models import Count, Exists, OuterRef, Q, Subquery
from django.forms.models import BaseInlineFormSet
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html, format_html_join
from django.utils.safestring import mark_safe
from django.utils.translation import gettext, gettext_lazy

logger = logging.getLogger(__name__)

from artworks.admin_filters import YearFilter, has_related_filter
from artworks.models import (
    ArtCurator,
    ArtCuratorTranslation,
    Artist,
    ArtistSocialLink,
    ArtistTranslation,
    Artwork,
    ArtworkGallery,
    ArtworkImage,
    ArtworkOrder,
    ArtworkOrderStatus,
    ArtworkStatus,
    ArtworkTranslation,
    Discipline,
    DisciplineTranslation,
    Format,
    FormatTranslation,
    Gallery,
    GalleryTranslation,
    Location,
    LocationTranslation,
    Scale,
    ScaleTranslation,
    Technique,
    TechniqueTranslation,
    Theme,
    ThemeTranslation,
)
from artworks import sale_notifications
from core.mail_utils import send_best_effort
from project.admin_base import ModelAdminUnfoldBase, TranslatableNameAdminMixin
from subscriptions.admin_helpers import subscription_badge, subscription_badge_from_artist
from subscriptions.models import ArtistSubscription, BillingPlan
from core.stripe_utils import epoch_to_datetime
from subscriptions.services import notifications, stripe_client
from core.stripe_compat import sget
from subscriptions.services.subscription_state import cash_renew_datetime, compute_is_active
from unfold.admin import StackedInline, TabularInline
from unfold.decorators import action


class TranslationInlineFormSet(BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        existing_langs = set()
        if self.instance and self.instance.pk:
            existing_langs = set(self.queryset.values_list("language", flat=True))
        available_langs = [code for code, name in settings.LANGUAGES if code not in existing_langs]
        for i, form in enumerate(self.extra_forms):
            if i < len(available_langs):
                form.initial["language"] = available_langs[i]

    def clean(self):
        super().clean()
        excluded = {"language", "DELETE", "id"}
        if self.fk:
            excluded.add(self.fk.name)
        filled = 0
        for form in self.forms:
            data = form.cleaned_data or {}
            if data.get("DELETE"):
                continue
            if any(value for key, value in data.items() if key not in excluded):
                filled += 1
        if filled != len(settings.LANGUAGES):
            labels = ", ".join(name for code, name in settings.LANGUAGES)
            raise ValidationError(
                f"Se requieren exactamente {len(settings.LANGUAGES)} traducciones ({labels})."
            )


class TranslationInline(StackedInline):
    formset = TranslationInlineFormSet
    verbose_name = "Traducción"
    verbose_name_plural = "Traducciones (Español / Inglés)"
    can_delete = False
    min_num = len(settings.LANGUAGES)
    max_num = len(settings.LANGUAGES)
    validate_min = True
    validate_max = True

    def get_extra(self, request, obj=None, **kwargs):
        if obj:
            existing_count = obj.translations.count()
            return max(0, len(settings.LANGUAGES) - existing_count)
        return len(settings.LANGUAGES)


class ArtistTranslationInline(TranslationInline):
    model = ArtistTranslation
    fields = ["language", "bio"]


class ArtistSocialLinkInline(TabularInline):
    model = ArtistSocialLink
    fields = ["platform", "url"]
    verbose_name = "Red social"
    verbose_name_plural = "Redes sociales"
    extra = 0


class ArtistSubscriptionInline(StackedInline):
    model = ArtistSubscription
    fk_name = "artist"
    verbose_name = "Suscripción"
    verbose_name_plural = "Suscripción"
    extra = 0
    max_num = 1
    min_num = 0
    can_delete = False
    show_change_link = True
    template = "admin/subscriptions/artistsubscription/edit_inline/stacked.html"
    fields = [
        "display_status",
        "stripe_customer_id",
        "stripe_subscription_id",
        "customer_email",
        "cash_last_paid_at",
        "current_period_end",
        "cancel_at_period_end",
        "display_signup_url",
        "signup_url_expires_at",
        "last_synced_at",
        "created_at",
        "updated_at",
        "display_raw_state",
    ]
    readonly_fields = fields

    @admin.display(description="Estado")
    def display_status(self, obj):
        if obj is None:
            return subscription_badge(None)
        return subscription_badge(obj)

    @admin.display(description="Link de pago")
    def display_signup_url(self, obj):
        if obj is None:
            return format_html('<span style="color:#6b7280">—</span>')
        url = getattr(obj, "signup_url", "") or ""
        expires_at = getattr(obj, "signup_url_expires_at", None)
        if not url:
            return format_html(
                '<span style="color:#6b7280">—</span> <span style="color:#991b1b;font-size:12px">(expirado)</span>'
            )
        # Reuse _link_is_valid semantics: valid when url exists and not expired
        is_expired = bool(expires_at and expires_at <= timezone.now())
        if is_expired:
            return format_html(
                '<a href="{}" target="_blank">{}</a> <span style="color:#991b1b;font-size:12px">(expirado)</span>',
                url,
                url,
            )
        # Valid: clickable + copy affordance
        return format_html(
            '<a href="{}" target="_blank">{}</a> <span data-copy-url="{}" style="margin-left:8px;cursor:pointer;color:#6b7280" title="Copiar link">⎘</span>',
            url,
            url,
            url,
        )

    @admin.display(description="Auditoría")
    def display_raw_state(self, obj):
        if obj is None or not getattr(obj, "raw_state", None):
            return format_html('<span style="color:#6b7280">—</span>')
        try:
            pretty = json.dumps(obj.raw_state, indent=2, ensure_ascii=False)
        except Exception:
            pretty = str(obj.raw_state)
        return format_html('<pre style="max-height:320px;overflow:auto">{}</pre>', pretty)

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class ArtCuratorTranslationInline(TranslationInline):
    model = ArtCuratorTranslation
    fields = ["language", "bio"]


class DisciplineTranslationInline(TranslationInline):
    model = DisciplineTranslation
    fields = ["language", "name"]


class TechniqueTranslationInline(TranslationInline):
    model = TechniqueTranslation
    fields = ["language", "name"]


class ThemeTranslationInline(TranslationInline):
    model = ThemeTranslation
    fields = ["language", "name"]


class FormatTranslationInline(TranslationInline):
    model = FormatTranslation
    fields = ["language", "name"]


class ScaleTranslationInline(TranslationInline):
    model = ScaleTranslation
    fields = ["language", "name"]


class GalleryTranslationInline(TranslationInline):
    model = GalleryTranslation
    fields = ["language", "name", "description"]


class LocationTranslationInline(TranslationInline):
    model = LocationTranslation
    fields = ["language", "name"]


class ArtworkGalleryInline(TabularInline):
    model = ArtworkGallery
    fields = ["artwork"]
    verbose_name = "Obra de arte"
    verbose_name_plural = "Obras de arte exhibidas"
    ordering_field = "sort_order"
    hide_ordering_field = True
    extra = 1


class GalleryArtworkInline(TabularInline):
    model = ArtworkGallery
    fields = ["gallery"]
    verbose_name = "Galería"
    verbose_name_plural = "Galerías donde se exhibe esta obra"
    ordering_field = "sort_order"
    hide_ordering_field = True
    extra = 1


class ArtistAvailableWorksFilter(admin.SimpleListFilter):
    title = "Obras disponibles"
    parameter_name = "has_available"

    def lookups(self, request, model_admin):
        return (
            ("with", "Con obras disponibles"),
            ("without", "Sin obras disponibles"),
        )

    def queryset(self, request, queryset):
        def has_available():
            return queryset.model.objects.filter(
                pk=OuterRef("pk"),
                artworks__is_active=True,
                artworks__status=ArtworkStatus.AVAILABLE,
            )

        if self.value() == "with":
            return queryset.filter(Exists(has_available()))
        if self.value() == "without":
            return queryset.filter(~Exists(has_available()))
        return queryset


class ArtistPaymentMethodFilter(admin.SimpleListFilter):
    title = "Método de pago"
    parameter_name = "payment_method"

    def lookups(self, request, model_admin):
        return (
            ("online", "En línea"),
            ("cash", "Efectivo"),
            ("none", "Sin suscripción"),
        )

    def queryset(self, request, queryset):
        if self.value() in ("online", "cash"):
            return queryset.filter(
                Exists(
                    ArtistSubscription.objects.filter(
                        artist=OuterRef("pk"), payment_method=self.value()
                    )
                )
            )
        if self.value() == "none":
            return queryset.filter(
                ~Exists(ArtistSubscription.objects.filter(artist=OuterRef("pk")))
            )
        return queryset


MSG_LINK_GENERATED = gettext_lazy("Link de suscripción generado.")
MSG_LINK_REGENERATED = gettext_lazy("Link regenerado.")
MSG_STALE_CUSTOMER = gettext_lazy("El customer fue eliminado de Stripe; regenera el link")


def _artist_redirect_url(artist):
    return reverse("admin:artworks_artist_change", args=[artist.pk])


def _billing_blocked(artist):
    if not artist.email:
        return gettext_lazy(
            "Este artista no tiene un correo electrónico. Captura uno antes de generar el link."
        )
    plan = BillingPlan.get_solo()
    if not plan.is_active_for_new_signups:
        return gettext_lazy("Las nuevas suscripciones están pausadas en el Plan de suscripción.")
    if not plan.stripe_price_id:
        return gettext_lazy(
            "Configura el precio (monto y moneda) en Plan de suscripción antes de generar links."
        )
    return None


@admin.register(Artist)
class ArtistAdmin(ModelAdminUnfoldBase):
    sidebar_icon = "palette"
    inlines = [ArtistTranslationInline, ArtistSocialLinkInline, ArtistSubscriptionInline]
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ["name", "email", "slug", "translations__bio"]
    list_filter = [
        ArtistPaymentMethodFilter,
        "is_active",
        "created_at",
        ("location", RelatedOnlyFieldListFilter),
        has_related_filter("artworks", "obras", "has_artworks"),
        ArtistAvailableWorksFilter,
    ]
    list_per_page = 50
    actions_detail = [
        "generate_link",
        "regenerate_link",
        "open_portal",
        "sync_from_stripe",
        "marcar_efectivo",
        "confirmar_pago",
        "cancelar_efectivo",
    ]

    def _resolve_artist(self, object_id):
        """Extract the real artist PK from a potentially greedy <path:object_id>.

        Unfold's action URLs use <path:object_id> which can capture '1/change'
        when the full path is '1/change/generate-link/'. This extracts the
        leading integer PK.
        """
        pk = object_id
        if isinstance(pk, str) and "/" in pk:
            pk = pk.split("/", 1)[0]
        return self.model.objects.get(pk=pk)

    def _link_exists(self, sub):
        """True when a subscription link has been generated (valid or expired)."""
        return bool(sub and sub.signup_url)

    def _link_is_valid(self, sub):
        """True when the subscription has a usable (non-expired) signup URL."""
        if not self._link_exists(sub):
            return False
        if sub.signup_url_expires_at and sub.signup_url_expires_at <= timezone.now():
            return False
        return True

    def change_view(self, request, object_id, form_url="", extra_context=None):
        extra_context = extra_context or {}
        artist = self.get_object(request, object_id)
        sub = getattr(artist, "subscription", None) if artist else None
        url = sub.signup_url if self._link_is_valid(sub) else None
        extra_context["copy_button_extra_attrs"] = (
            mark_safe(f'type="button" data-copy-url="{url}"') if url else None
        )
        return super().change_view(request, object_id, form_url, extra_context)
    fieldsets = (
        ("Datos personales", {
            "fields": (("name", "slug"), ("birth_year", "death_year"), "location")
        }),
        ("Contacto y medios", {
            "fields": ("email", "website", "photo")
        }),
        ("Resumen", {
            "fields": (
                "display_techniques_detail",
                "display_available_detail",
                "display_new_additions_detail",
                "display_highlighted_detail",
                "display_most_viewed_detail",
                "display_curations_detail",
            )
        }),
        ("Estado del sistema", {
            "fields": (("is_active",),)
        }),
    )
    readonly_fields = [
        "display_techniques_detail",
        "display_available_detail",
        "display_new_additions_detail",
        "display_highlighted_detail",
        "display_most_viewed_detail",
        "display_curations_detail",
    ]
    list_display = [
        "display_name",
        "display_email",
        "display_active",
        "subscription_status_badge",
        "display_artworks_count",
        "display_available_count",
        "display_galleries_count",
    ]

    def get_queryset(self, request):
        subscription_exists = Exists(
            ArtistSubscription.objects.filter(artist=OuterRef("pk"))
        )
        subscription_status = Subquery(
            ArtistSubscription.objects.filter(artist=OuterRef("pk")).values("status")[:1]
        )
        subscription_payment_method = Subquery(
            ArtistSubscription.objects.filter(artist=OuterRef("pk")).values(
                "payment_method"
            )[:1]
        )
        return (
            super().get_queryset(request)
            .annotate(
                _has_subscription=subscription_exists,
                _subscription_status=subscription_status,
                _payment_method=subscription_payment_method,
            )
            .annotate(
                _artworks_count=Count("artworks", filter=Q(artworks__is_active=True), distinct=True),
                _available_count=Count(
                    "artworks",
                    filter=Q(artworks__is_active=True, artworks__status=ArtworkStatus.AVAILABLE),
                    distinct=True,
                ),
                _techniques_count=Count("artworks__techniques", distinct=True),
                _highlighted_count=Count(
                    "artworks",
                    filter=Q(artworks__is_active=True, artworks__is_highlighted=True),
                    distinct=True,
                ),
                _galleries_count=Count(
                    "artworks__gallery_links__gallery",
                    filter=Q(artworks__gallery_links__gallery__is_active=True),
                    distinct=True,
                ),
            )
        )

    @admin.display(description="Nombre", ordering="name")
    def display_name(self, obj):
        return obj.name

    @admin.display(description="Correo electrónico", ordering="email")
    def display_email(self, obj):
        return obj.email or "-"

    @admin.display(description="Activo", ordering="is_active", boolean=True)
    def display_active(self, obj):
        return obj.is_active

    @admin.display(description="Suscripción")
    def subscription_status_badge(self, obj):
        return subscription_badge_from_artist(obj)

    # -- Permission methods (conditional button visibility) --

    def has_generate_link_permission(self, request, object_id):
        artist = self._resolve_artist(object_id)
        sub = getattr(artist, "subscription", None)
        if self._is_cash_sub(sub) and sub.status != ArtistSubscription.Status.CANCELED:
            return False
        return not self._link_exists(sub)

    def has_regenerate_link_permission(self, request, object_id):
        artist = self._resolve_artist(object_id)
        sub = getattr(artist, "subscription", None)
        return self._link_exists(sub) and not self._is_cash_sub(sub)

    def has_open_portal_permission(self, request, object_id):
        artist = self._resolve_artist(object_id)
        sub = getattr(artist, "subscription", None)
        return self._link_exists(sub) and not self._is_cash_sub(sub)

    def has_sync_from_stripe_permission(self, request, object_id):
        artist = self._resolve_artist(object_id)
        sub = getattr(artist, "subscription", None)
        return not self._is_cash_sub(sub)

    def _is_cash_sub(self, sub):
        """True when the subscription row is on the manual cash path."""
        return bool(sub and sub.payment_method == ArtistSubscription.PaymentMethod.CASH)

    def _has_active_stripe_billing(self, sub):
        """True when the online row is actively billing (blocks cash conversion).

        Status-driven: only actively-billing online rows block a switch to cash.
        Never-paid (`pending`), `canceled`, `canceling`, and cancel-requested
        (`active` with `cancel_at_period_end`) rows may convert to cash.
        """
        if not (sub and sub.payment_method == ArtistSubscription.PaymentMethod.ONLINE):
            return False
        if sub.status == ArtistSubscription.Status.PAST_DUE:
            return True
        return (
            sub.status == ArtistSubscription.Status.ACTIVE
            and not sub.cancel_at_period_end
        )

    def has_marcar_efectivo_permission(self, request, object_id):
        artist = self._resolve_artist(object_id)
        sub = getattr(artist, "subscription", None)
        if sub is None:
            return True
        if self._is_cash_sub(sub):
            return sub.status == ArtistSubscription.Status.CANCELED
        # Only actively-billing online rows block cash conversion.
        return not self._has_active_stripe_billing(sub)

    def has_confirmar_pago_permission(self, request, object_id):
        artist = self._resolve_artist(object_id)
        sub = getattr(artist, "subscription", None)
        return self._is_cash_sub(sub) and sub.status in (
            ArtistSubscription.Status.PENDING,
            ArtistSubscription.Status.ACTIVE,
            ArtistSubscription.Status.PAST_DUE,
        )

    def has_cancelar_efectivo_permission(self, request, object_id):
        artist = self._resolve_artist(object_id)
        sub = getattr(artist, "subscription", None)
        return self._is_cash_sub(sub) and sub.status in (
            ArtistSubscription.Status.PENDING,
            ArtistSubscription.Status.ACTIVE,
            ArtistSubscription.Status.PAST_DUE,
        )

    # -- Actions_detail methods --

    def _refuse_cash_on_stripe_path(self, request, redirect_url, artist):
        """Refuse a Stripe action for cash pending/active rows (direct-URL guard)."""
        sub = getattr(artist, "subscription", None)
        if self._is_cash_sub(sub) and sub.status != ArtistSubscription.Status.CANCELED:
            messages.error(request, gettext("Este artista paga en efectivo. Esta acción de Stripe no aplica."))
            return redirect(redirect_url)
        return None

    def _is_stale_customer_error(self, e, customer_id):
        """True when a Stripe error means the stored customer is missing/deleted.

        Grounded on the Stripe SDK (pinned >=15.5.1,<16): the checkouts/billing
        endpoints report a nonexistent/deleted customer as an
        `InvalidRequestError` with `code == "resource_missing"` and/or the
        customer id surfacing in the error text/`param`. Falls back to matching
        the stored id in the message so a shape change degrades to the generic
        error path rather than mis-recovering.
        """
        if not isinstance(e, stripe.error.InvalidRequestError):
            return False
        if e.code == "resource_missing":
            return True
        if customer_id and (
            (getattr(e, "param", None) or "").lower() == "customer"
            or customer_id in str(e)
        ):
            return True
        return False

    def _create_session_recovering_stale_customer(self, sub, artist, price_id):
        """Create a checkout session, recreating a deleted/dangling customer once.

        Uses the stored `stripe_customer_id` (creating one when missing). If the
        checkout call reveals that customer as missing/deleted in Stripe, clears
        the stale id, creates a fresh customer, and retries once. Any other
        `StripeError` propagates to the caller's generic error path.
        """
        for attempt in range(2):
            try:
                if not sub.stripe_customer_id:
                    customer = stripe_client.create_customer(artist.email)
                    sub.stripe_customer_id = customer.id
                return stripe_client.create_checkout_session(
                    sub.stripe_customer_id, {"artist_id": str(artist.pk)}, price_id
                )
            except stripe.error.StripeError as e:
                if attempt == 0 and self._is_stale_customer_error(e, sub.stripe_customer_id):
                    sub.stripe_customer_id = None
                    continue
                raise

    @action(description="Generar link de suscripción", url_path="generate-link", permissions=["generate_link"])
    def generate_link(self, request, object_id):
        artist = self._resolve_artist(object_id)
        redirect_url = _artist_redirect_url(artist)

        refused = self._refuse_cash_on_stripe_path(request, redirect_url, artist)
        if refused is not None:
            return refused

        blocked = _billing_blocked(artist)
        if blocked:
            messages.error(request, blocked)
            return redirect(redirect_url)

        plan = BillingPlan.get_solo()
        sub, _created = ArtistSubscription.objects.get_or_create(
            artist=artist,
            defaults={"status": ArtistSubscription.Status.PENDING},
        )
        if self._is_cash_sub(sub):
            # Re-entering the online flow: drop the cash path so Stripe
            # webhooks track this row again (never a hybrid cash+Stripe row).
            sub.payment_method = ArtistSubscription.PaymentMethod.ONLINE
            sub.status = ArtistSubscription.Status.PENDING
            sub.cash_last_paid_at = None
            sub.raw_state = {}

        try:
            session = self._create_session_recovering_stale_customer(sub, artist, plan.stripe_price_id)
        except stripe.error.StripeError as e:
            logger.warning("generate_link artist=%s StripeError: %s", artist.pk, e)
            messages.error(request, f"Stripe no respondió: {e}")
            return redirect(redirect_url)
        sub.signup_url = session.url
        sub.signup_url_expires_at = epoch_to_datetime(session.expires_at)
        sub.status = ArtistSubscription.Status.PENDING
        sub.last_synced_at = timezone.now()
        sub.save(
            update_fields=[
                "payment_method",
                "signup_url",
                "signup_url_expires_at",
                "status",
                "cash_last_paid_at",
                "raw_state",
                "last_synced_at",
                "stripe_customer_id",
                "updated_at",
            ]
        )

        artist.is_active = compute_is_active(sub)
        artist.save(update_fields=["is_active", "updated_at"])

        messages.success(request, MSG_LINK_GENERATED)
        return redirect(redirect_url)

    @action(description="Regenerar link", url_path="regenerate-link", permissions=["regenerate_link"])
    def regenerate_link(self, request, object_id):
        artist = self._resolve_artist(object_id)
        redirect_url = _artist_redirect_url(artist)

        refused = self._refuse_cash_on_stripe_path(request, redirect_url, artist)
        if refused is not None:
            return refused

        blocked = _billing_blocked(artist)
        if blocked:
            messages.error(request, blocked)
            return redirect(redirect_url)

        sub = ArtistSubscription.objects.filter(artist=artist).first()
        if sub is None:
            return self.generate_link(request, object_id)

        existing = stripe_client.expire_or_reuse_session(
            sub.signup_url, sub.signup_url_expires_at
        )
        if existing:
            messages.success(request, MSG_LINK_REGENERATED)
            return redirect(redirect_url)

        plan = BillingPlan.get_solo()
        try:
            session = self._create_session_recovering_stale_customer(sub, artist, plan.stripe_price_id)
        except stripe.error.StripeError as e:
            logger.warning("regenerate_link artist=%s StripeError: %s", artist.pk, e)
            messages.error(request, f"Stripe no respondió: {e}")
            return redirect(redirect_url)
        sub.signup_url = session.url
        sub.signup_url_expires_at = epoch_to_datetime(session.expires_at)
        sub.last_synced_at = timezone.now()
        sub.save(
            update_fields=[
                "signup_url",
                "signup_url_expires_at",
                "last_synced_at",
                "stripe_customer_id",
                "updated_at",
            ]
        )

        messages.success(request, MSG_LINK_REGENERATED)
        return redirect(redirect_url)

    @action(description="Abrir Customer Portal", url_path="open-portal", permissions=["open_portal"], attrs={"target": "_blank"})
    def open_portal(self, request, object_id):
        artist = self._resolve_artist(object_id)
        redirect_url = _artist_redirect_url(artist)

        sub = ArtistSubscription.objects.filter(artist=artist).first()
        if self._is_cash_sub(sub) and sub.status != ArtistSubscription.Status.CANCELED:
            messages.warning(request, gettext("Este artista paga en efectivo. Esta acción de Stripe no aplica."))
            return redirect(redirect_url)
        if sub is None or not sub.stripe_customer_id:
            messages.warning(request, gettext("Aún no se generó un link de pago para este artista."))
            return redirect(redirect_url)

        try:
            session = stripe_client.create_billing_portal_session(sub.stripe_customer_id)
        except stripe.error.StripeError as e:
            if self._is_stale_customer_error(e, sub.stripe_customer_id):
                sub.stripe_customer_id = None
                sub.save(update_fields=["stripe_customer_id", "updated_at"])
                messages.warning(request, MSG_STALE_CUSTOMER)
                return redirect(redirect_url)
            logger.warning("open_portal artist=%s StripeError: %s", artist.pk, e)
            messages.error(request, f"Stripe no respondió: {e}")
            return redirect(redirect_url)
        return redirect(session.url)

    @action(description="Sincronizar desde Stripe", url_path="sync-from-stripe", permissions=["sync_from_stripe"])
    def sync_from_stripe(self, request, object_id):
        artist = self._resolve_artist(object_id)
        redirect_url = _artist_redirect_url(artist)

        sub = ArtistSubscription.objects.filter(artist=artist).first()
        if self._is_cash_sub(sub):
            messages.warning(request, gettext("Este artista paga en efectivo. Esta acción de Stripe no aplica."))
            return redirect(redirect_url)
        if sub is None or not sub.stripe_customer_id:
            messages.warning(request, gettext("Este artista aún no tiene un customer en Stripe."))
            return redirect(redirect_url)

        prev_label = sub.get_status_display()
        try:
            customer = stripe_client.fetch_customer(sub.stripe_customer_id)
            subs = stripe_client.list_subscriptions(sub.stripe_customer_id, limit=1)
        except stripe.error.StripeError as e:
            if self._is_stale_customer_error(e, sub.stripe_customer_id):
                sub.stripe_customer_id = None
                sub.save(update_fields=["stripe_customer_id", "updated_at"])
                messages.warning(request, MSG_STALE_CUSTOMER)
                return redirect(redirect_url)
            logger.warning("sync_from_stripe artist=%s StripeError: %s", artist.pk, e)
            messages.error(request, f"Stripe no respondió: {e}")
            return redirect(redirect_url)
        if sget(customer, "deleted"):
            # A customer deleted in Stripe retrieves as a `deleted` marker
            # (no exception); clear the dangling id and point the operator at
            # regenerating the link rather than leaving a dead pointer.
            sub.stripe_customer_id = None
            sub.save(update_fields=["stripe_customer_id", "updated_at"])
            messages.warning(request, MSG_STALE_CUSTOMER)
            return redirect(redirect_url)
        sub.customer_email = sget(customer, "email") or sub.customer_email

        subs_data = subs.data if hasattr(subs, "data") else subs
        if not subs_data:
            if sub.status != ArtistSubscription.Status.PENDING:
                sub.status = ArtistSubscription.Status.CANCELED
            sub.last_synced_at = timezone.now()
            sub.save(
                update_fields=["status", "customer_email", "last_synced_at", "updated_at"]
            )
        else:
            sub.apply_stripe_payload(subs_data[0])

        artist.is_active = compute_is_active(sub)
        artist.save(update_fields=["is_active", "updated_at"])

        messages.success(
            request,
            gettext("Suscripción sincronizada: {prev} → {new}").format(
                prev=prev_label, new=sub.get_status_display()
            ),
        )
        return redirect(redirect_url)

    def _notify_cash(self, request, redirect_url, kind, artist, success_message):
        """Send cash emails; on failure keep state and warn (never rollback)."""
        try:
            getattr(notifications, f"send_cash_{kind}")(artist, request.user)
        except Exception:
            logger.exception("cash email %s failed artist=%s", kind, artist.pk)
            messages.warning(request, gettext("Estado guardado, pero el correo falló. Reintenta el envío manualmente."))
            return redirect(redirect_url)
        messages.success(request, success_message)
        return redirect(redirect_url)

    @action(description="Marcar como efectivo", url_path="marcar-efectivo", permissions=["marcar_efectivo"])
    def marcar_efectivo(self, request, object_id):
        artist = self._resolve_artist(object_id)
        redirect_url = _artist_redirect_url(artist)

        if not artist.email:
            messages.error(request, gettext("Este artista no tiene un correo electrónico. Captura uno antes de marcarlo como efectivo."))
            return redirect(redirect_url)

        sub = ArtistSubscription.objects.filter(artist=artist).first()
        if sub is not None and (
            self._has_active_stripe_billing(sub)
            or (self._is_cash_sub(sub) and sub.status != ArtistSubscription.Status.CANCELED)
        ):
            messages.error(request, gettext("Este artista tiene una suscripción en línea activa. Cancélala en Stripe antes de marcarlo como efectivo."))
            return redirect(redirect_url)

        sub, _created = ArtistSubscription.objects.get_or_create(
            artist=artist,
            defaults={
                "status": ArtistSubscription.Status.PENDING,
                "payment_method": ArtistSubscription.PaymentMethod.CASH,
            },
        )
        sub.payment_method = ArtistSubscription.PaymentMethod.CASH
        sub.status = ArtistSubscription.Status.PENDING
        sub.signup_url = ""
        sub.signup_url_expires_at = None
        # Cash rows carry no Stripe linkage; drop any pointer (None, not "",
        # because stripe_customer_id/stripe_subscription_id are unique-nullable).
        sub.stripe_customer_id = None
        sub.stripe_subscription_id = None
        # Fresh cycle: drop any dates from a previous canceled period.
        sub.cash_last_paid_at = None
        sub.current_period_end = None
        sub.raw_state = {"cash": True, "marked_by": request.user.get_username()}
        sub.last_synced_at = timezone.now()
        sub.save(
            update_fields=[
                "payment_method",
                "status",
                "signup_url",
                "signup_url_expires_at",
                "stripe_customer_id",
                "stripe_subscription_id",
                "cash_last_paid_at",
                "current_period_end",
                "raw_state",
                "last_synced_at",
                "updated_at",
            ]
        )

        artist.is_active = compute_is_active(sub)
        artist.save(update_fields=["is_active", "updated_at"])

        return self._notify_cash(
            request, redirect_url, "pending", artist,
            gettext("Artista registrado para pago en efectivo. Pendiente de confirmación."),
        )

    @action(description="Confirmar pago", url_path="confirmar-pago-efectivo", permissions=["confirmar_pago"])
    def confirmar_pago(self, request, object_id):
        artist = self._resolve_artist(object_id)
        redirect_url = _artist_redirect_url(artist)

        sub = ArtistSubscription.objects.filter(artist=artist).first()
        if (
            sub is None
            or not self._is_cash_sub(sub)
            or sub.status
            not in (
                ArtistSubscription.Status.PENDING,
                ArtistSubscription.Status.ACTIVE,
                ArtistSubscription.Status.PAST_DUE,
            )
        ):
            messages.error(request, gettext("Este artista no tiene un pago en efectivo pendiente de confirmación."))
            return redirect(redirect_url)

        # Each execution counts as one monthly payment: stamp the paid date
        # and push the renew date one calendar month from the later of today
        # and the current renew date (early payers keep their full period).
        today = timezone.localdate()
        current = sub.current_period_end
        current_renew = timezone.localdate(current) if current is not None else None
        base = max(today, current_renew) if current_renew is not None else today
        sub.status = ArtistSubscription.Status.ACTIVE
        sub.cash_last_paid_at = today
        sub.current_period_end = cash_renew_datetime(base)
        sub.raw_state = {"cash": True, "confirmed_by": request.user.get_username()}
        sub.last_synced_at = timezone.now()
        sub.save(
            update_fields=[
                "status",
                "cash_last_paid_at",
                "current_period_end",
                "raw_state",
                "last_synced_at",
                "updated_at",
            ]
        )

        artist.is_active = compute_is_active(sub)
        artist.save(update_fields=["is_active", "updated_at"])

        return self._notify_cash(
            request, redirect_url, "active", artist,
            gettext("Pago en efectivo confirmado. El artista ya es visible."),
        )

    @action(description="Cancelar efectivo", url_path="cancelar-efectivo", permissions=["cancelar_efectivo"])
    def cancelar_efectivo(self, request, object_id):
        artist = self._resolve_artist(object_id)
        redirect_url = _artist_redirect_url(artist)

        sub = ArtistSubscription.objects.filter(artist=artist).first()
        if (
            sub is None
            or not self._is_cash_sub(sub)
            or sub.status
            not in (
                ArtistSubscription.Status.PENDING,
                ArtistSubscription.Status.ACTIVE,
                ArtistSubscription.Status.PAST_DUE,
            )
        ):
            messages.error(request, gettext("Este artista no tiene una suscripción en efectivo vigente."))
            return redirect(redirect_url)

        sub.status = ArtistSubscription.Status.CANCELED
        sub.raw_state = {"cash": True, "canceled_by": request.user.get_username()}
        sub.last_synced_at = timezone.now()
        sub.save(update_fields=["status", "raw_state", "last_synced_at", "updated_at"])

        artist.is_active = compute_is_active(sub)
        artist.save(update_fields=["is_active", "updated_at"])

        return self._notify_cash(
            request, redirect_url, "canceled", artist,
            gettext("Suscripción en efectivo cancelada. El artista ya no es visible."),
        )

    class Media:
        js = ["js/copy_clipboard.js"]

    @staticmethod
    def _translated_name(holder):
        es = holder.translations.filter(language="es").first()
        if es:
            return es.name
        first = holder.translations.first()
        return first.name if first else "-"

    @staticmethod
    def _artwork_title(artwork):
        es = artwork.translations.filter(language="es").first()
        if es:
            return es.title
        first = artwork.translations.first()
        return first.title if first else artwork.slug

    @admin.display(description="Obras")
    def display_artworks_count(self, obj):
        return obj._artworks_count

    @admin.display(description="Disponibles")
    def display_available_count(self, obj):
        return obj._available_count

    @admin.display(description="Técnicas")
    def display_techniques_count(self, obj):
        return obj._techniques_count

    @admin.display(description="Destacadas")
    def display_highlighted_count(self, obj):
        return obj._highlighted_count

    @admin.display(description="Galerías")
    def display_galleries_count(self, obj):
        return obj._galleries_count

    @admin.display(description="Técnicas")
    def display_techniques_detail(self, obj):
        names = [self._translated_name(t) for t in obj.techniques]
        return ", ".join(names) if names else "-"

    @admin.display(description="Obras disponibles")
    def display_available_detail(self, obj):
        return f"{obj.available_artworks.count()} obra(s) disponible(s)"

    @admin.display(description="Nuevas incorporaciones")
    def display_new_additions_detail(self, obj):
        rows = [(self._artwork_title(a), a.year) for a in obj.new_additions]
        if not rows:
            return "-"
        return format_html_join("", "<div>- {0} ({1})</div>", rows)

    @admin.display(description="Destacadas")
    def display_highlighted_detail(self, obj):
        titles = [self._artwork_title(a) for a in obj.highlighted_artworks]
        if not titles:
            return "-"
        return format_html_join("", "<div>- {0}</div>", [(t,) for t in titles])

    @admin.display(description="Más visitadas")
    def display_most_viewed_detail(self, obj):
        rows = [(self._artwork_title(a), a.views_count) for a in obj.most_viewed]
        if not rows:
            return "-"
        return format_html_join("", "<div>- {0} — {1} visitas</div>", rows)

    @admin.display(description="Curadurías (galerías)")
    def display_curations_detail(self, obj):
        names = [self._translated_name(g) for g in obj.curations]
        return ", ".join(names) if names else "-"


@admin.register(ArtCurator)
class ArtCuratorAdmin(ModelAdminUnfoldBase):
    sidebar_icon = "person_check"
    inlines = [ArtCuratorTranslationInline]
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ["name", "email", "slug", "translations__bio"]
    list_filter = [
        "is_active",
        has_related_filter("curated_galleries", "galerías", "has_galleries"),
    ]
    fieldsets = (
        ("Datos personales", {
            "fields": (("name", "slug"),)
        }),
        ("Contacto y medios", {
            "fields": ("email", "website", "photo")
        }),
        ("Estado del sistema", {
            "fields": (("is_active",),)
        }),
    )
    list_display = [
        "display_name",
        "display_email",
        "display_active",
    ]

    @admin.display(description="Nombre", ordering="name")
    def display_name(self, obj):
        return obj.name

    @admin.display(description="Correo electrónico", ordering="email")
    def display_email(self, obj):
        return obj.email or "-"

    @admin.display(description="Activo", ordering="is_active", boolean=True)
    def display_active(self, obj):
        return obj.is_active


@admin.register(Discipline)
class DisciplineAdmin(TranslatableNameAdminMixin, ModelAdminUnfoldBase):
    sidebar_icon = "label"
    inlines = [DisciplineTranslationInline]
    search_fields = ["slug", "translations__name"]
    list_filter = [
        "is_active",
        has_related_filter("artworks", "obras", "has_artworks"),
    ]
    fieldsets = (
        ("Información del sistema", {
            "fields": ("slug", "is_active")
        }),
    )
    list_display = ["display_name", "slug", "display_active"]

    @admin.display(description="Activo", ordering="is_active", boolean=True)
    def display_active(self, obj):
        return obj.is_active


@admin.register(Technique)
class TechniqueAdmin(TranslatableNameAdminMixin, ModelAdminUnfoldBase):
    sidebar_icon = "brush"
    inlines = [TechniqueTranslationInline]
    search_fields = ["slug", "translations__name"]
    list_filter = [
        "is_active",
        has_related_filter("artworks", "obras", "has_artworks"),
    ]
    fieldsets = (
        ("Información del sistema", {
            "fields": ("slug", "is_active")
        }),
    )
    list_display = ["display_name", "slug", "display_active"]

    @admin.display(description="Activo", ordering="is_active", boolean=True)
    def display_active(self, obj):
        return obj.is_active


@admin.register(Theme)
class ThemeAdmin(TranslatableNameAdminMixin, ModelAdminUnfoldBase):
    sidebar_icon = "topic"
    inlines = [ThemeTranslationInline]
    search_fields = ["slug", "translations__name"]
    list_filter = [
        "is_active",
        has_related_filter("artworks", "obras", "has_artworks"),
    ]
    fieldsets = (
        ("Información del sistema", {
            "fields": ("slug", "is_active")
        }),
    )
    list_display = ["display_name", "slug", "display_active"]

    @admin.display(description="Activo", ordering="is_active", boolean=True)
    def display_active(self, obj):
        return obj.is_active


@admin.register(Format)
class FormatAdmin(TranslatableNameAdminMixin, ModelAdminUnfoldBase):
    sidebar_icon = "view_module"
    inlines = [FormatTranslationInline]
    search_fields = ["slug", "translations__name"]
    list_filter = [
        "is_active",
        has_related_filter("artworks", "obras", "has_artworks"),
    ]
    fieldsets = (
        ("Información del sistema", {
            "fields": ("slug", "is_active")
        }),
    )
    list_display = ["display_name", "slug", "display_active"]

    @admin.display(description="Activo", ordering="is_active", boolean=True)
    def display_active(self, obj):
        return obj.is_active


@admin.register(Scale)
class ScaleAdmin(TranslatableNameAdminMixin, ModelAdminUnfoldBase):
    sidebar_icon = "straighten"
    inlines = [ScaleTranslationInline]
    search_fields = ["slug", "translations__name"]
    list_filter = [
        "is_active",
        has_related_filter("artworks", "obras", "has_artworks"),
    ]
    fieldsets = (
        ("Información del sistema", {
            "fields": ("slug", "is_active")
        }),
    )
    list_display = ["display_name", "slug", "display_active"]

    @admin.display(description="Activo", ordering="is_active", boolean=True)
    def display_active(self, obj):
        return obj.is_active


@admin.register(Location)
class LocationAdmin(TranslatableNameAdminMixin, ModelAdminUnfoldBase):
    sidebar_icon = "location_on"
    inlines = [LocationTranslationInline]
    search_fields = ["slug", "translations__name"]
    list_filter = [
        "is_active",
        has_related_filter("artworks", "obras", "has_artworks"),
    ]
    fieldsets = (
        ("Información del sistema", {
            "fields": ("slug", "is_active")
        }),
    )
    list_display = ["display_name", "slug", "display_active"]

    @admin.display(description="Activo", ordering="is_active", boolean=True)
    def display_active(self, obj):
        return obj.is_active


class GalleryAdminForm(forms.ModelForm):
    class Meta:
        model = Gallery
        fields = "__all__"

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("is_primary", False):
            Gallery.objects.filter(is_primary=True).exclude(pk=self.instance.pk).update(is_primary=False)
        return cleaned


@admin.register(Gallery)
class GalleryAdmin(TranslatableNameAdminMixin, ModelAdminUnfoldBase):
    sidebar_icon = "storefront"
    form = GalleryAdminForm
    inlines = [GalleryTranslationInline, ArtworkGalleryInline]
    search_fields = ["slug", "translations__name", "translations__description"]
    list_filter = [
        "is_active",
        ("curator", RelatedOnlyFieldListFilter),
        has_related_filter("artwork_links", "obras", "has_artworks"),
    ]
    fieldsets = (
        ("Información básica", {
            "fields": ("curator", "logo", "is_primary")
        }),
        ("Información del sistema", {
            "fields": ("slug", "is_active")
        }),
    )
    list_display = ["display_name", "slug", "curator", "display_is_primary", "display_active"]
    list_filter = [
        "is_active",
        "is_primary",
        ("curator", RelatedOnlyFieldListFilter),
        has_related_filter("artwork_links", "obras", "has_artworks"),
    ]

    @admin.display(description="Activo", ordering="is_active", boolean=True)
    def display_active(self, obj):
        return obj.is_active

    @admin.display(description="Principal", ordering="is_primary", boolean=True)
    def display_is_primary(self, obj):
        return obj.is_primary


class ArtworkTranslationInline(TranslationInline):
    model = ArtworkTranslation
    fields = ["language", "title", "description"]


class ArtworkImageInline(TabularInline):
    model = ArtworkImage
    fields = ["image", "alt_es", "alt_en", "is_primary"]
    ordering_field = "sort_order"
    hide_ordering_field = True
    extra = 0


@admin.register(Artwork)
class ArtworkAdmin(ModelAdminUnfoldBase):
    sidebar_icon = "palette"
    inlines = [ArtworkTranslationInline, ArtworkImageInline, GalleryArtworkInline]
    search_fields = [
        "slug",
        "translations__title",
        "artist__name",
        "disciplines__translations__name",
        "techniques__translations__name",
        "themes__translations__name",
        "formats__translations__name",
        "scales__translations__name",
    ]
    list_filter = [
        "status",
        "is_active",
        "is_highlighted",
        "created_at",
        ("artist", RelatedOnlyFieldListFilter),
        ("gallery_links__gallery", RelatedOnlyFieldListFilter),
        YearFilter,
        ("disciplines", RelatedOnlyFieldListFilter),
        ("techniques", RelatedOnlyFieldListFilter),
        ("themes", RelatedOnlyFieldListFilter),
        ("formats", RelatedOnlyFieldListFilter),
        ("scales", RelatedOnlyFieldListFilter),
    ]
    autocomplete_fields = ["disciplines", "techniques", "themes", "formats", "scales"]
    list_per_page = 25
    fieldsets = (
        ("Atributos principales", {
            "fields": (("artist", "year"), "dimensions")
        }),
        ("Taxonomías", {
            "fields": (
                "disciplines",
                "techniques",
                "themes",
                "formats",
                "scales",
            )
        }),
        ("Comercial y estado", {
            "fields": (("price_mxn", "price_usd"), "status", ("is_highlighted", "views_count"))
        }),
        ("Configuración del sistema", {
            "fields": ("slug", "is_active")
        }),
    )
    list_display = [
        "display_image",
        "display_title",
        "status",
        "display_active",
        "artist",
        "display_taxonomies",
        "display_price",
        "is_highlighted",
    ]

    def get_queryset(self, request):
        return (
            super().get_queryset(request)
            .prefetch_related(
                "images",
                "translations",
                "disciplines__translations",
                "techniques__translations",
                "themes__translations",
                "formats__translations",
                "scales__translations",
            )
        )

    @admin.display(description="Imagen")
    def display_image(self, obj):
        images = list(obj.images.all())
        img = next((i for i in images if i.is_primary), None) or (images[0] if images else None)
        if img and img.image:
            return format_html('<img src="{}" class="img-preview img-preview--sm" />', img.image.url)
        return "-"

    @admin.display(description="Título")
    def display_title(self, obj):
        translations = list(obj.translations.all())
        es = next((t for t in translations if t.language == "es"), None)
        if es:
            return es.title
        return translations[0].title if translations else "-"

    @admin.display(description="Clasificación")
    def display_taxonomies(self, obj):
        labels = []
        for name in ("disciplines", "techniques", "themes", "formats", "scales"):
            values = list(getattr(obj, name).all())
            if values:
                names = []
                for v in values:
                    translations = list(v.translations.all())
                    es = next((t for t in translations if t.language == "es"), None)
                    t = es or (translations[0] if translations else None)
                    if t:
                        names.append(t.name)
                if names:
                    labels.append(", ".join(names))
        text = ", ".join(labels) or "-"
        if text == "-" or len(text) <= 60:
            return text
        return format_html('<span title="{}">{}…</span>', text, text[:59])

    @admin.display(description="Precio")
    def display_price(self, obj):
        return f"${obj.price_mxn:,.2f} MXN / ${obj.price_usd:,.2f} USD"

    @admin.display(description="Activo", ordering="is_active", boolean=True)
    def display_active(self, obj):
        return obj.is_active


class ArtworkOrderInline(TabularInline):
    model = ArtworkOrder
    extra = 0
    max_num = 0
    can_delete = False
    show_change_link = True
    readonly_fields = ("slug", "status", "currency", "amount", "buyer_email", "paid_at", "created_at")
    fields = ("slug", "status", "currency", "amount", "buyer_email", "paid_at", "created_at")

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(ArtworkOrder)
class ArtworkOrderAdmin(ModelAdminUnfoldBase):
    sidebar_icon = "shopping_bag"
    list_display = ("slug", "artwork", "status", "currency", "amount", "buyer_email", "paid_at", "created_at")
    list_filter = ("status", "currency", "created_at", "paid_at")
    date_hierarchy = "created_at"
    search_fields = ("slug", "buyer_email", "artwork__translations__title", "stripe_checkout_session_id")
    readonly_fields = (
        "slug", "artwork", "status", "currency", "amount",
        "stripe_checkout_session_id", "checkout_url", "session_expires_at",
        "stripe_payment_intent_id", "buyer_email", "buyer_name",
        "paid_at", "cancelled_at", "created_at", "updated_at",
    )
    fieldsets = (
        ("Pedido", {"fields": ("artwork", "status", "currency", "amount")}),
        ("Stripe y comprador", {"fields": (
            "stripe_checkout_session_id", "checkout_url", "session_expires_at",
            "stripe_payment_intent_id", "buyer_email", "buyer_name",
            "paid_at", "cancelled_at",
        )}),
        ("Datos de entrega", {"fields": (
            "receiver_name", "receiver_phone", "country", "state", "city",
            "postal_code", "neighborhood", "street", "exterior_number",
            "interior_number", "between_street_1", "between_street_2",
            "reference", "delivery_notes",
        )}),
        ("Sistema", {"fields": ("slug", "is_active", "created_at", "updated_at")}),
    )
    actions = ["marcar_enviada", "marcar_entregada", "liberar_reserva"]

    @admin.action(description="Marcar enviada")
    def marcar_enviada(self, request, queryset):
        eligible = list(queryset.filter(status=ArtworkOrderStatus.DATA_COMPLETE).values_list("id", flat=True))
        ok = queryset.filter(id__in=eligible).update(status=ArtworkOrderStatus.SHIPPED)
        bad = queryset.count() - ok
        if bad:
            self.message_user(request, f"{bad} pedido(s) no estaban en Datos completos.", messages.ERROR)
        if ok:
            changed = ArtworkOrder.objects.filter(id__in=eligible)
            for order in changed:
                send_best_effort(sale_notifications.send_sale_shipped, order)
            self.message_user(request, f"{ok} pedido(s) marcados como enviados.", messages.SUCCESS)

    @admin.action(description="Marcar entregada")
    def marcar_entregada(self, request, queryset):
        eligible = list(queryset.filter(status=ArtworkOrderStatus.SHIPPED).values_list("id", flat=True))
        ok = queryset.filter(id__in=eligible).update(status=ArtworkOrderStatus.DELIVERED)
        bad = queryset.count() - ok
        if bad:
            self.message_user(request, f"{bad} pedido(s) no estaban Enviados.", messages.ERROR)
        if ok:
            changed = ArtworkOrder.objects.filter(id__in=eligible)
            for order in changed:
                send_best_effort(sale_notifications.send_sale_delivered, order)
            self.message_user(request, f"{ok} pedido(s) marcados como entregados.", messages.SUCCESS)

    @admin.action(description="Liberar reserva")
    def liberar_reserva(self, request, queryset):
        from artworks.models import ArtworkStatus as _AS

        ok = 0
        bad = 0
        for order in queryset.select_related("artwork"):
            if order.status != ArtworkOrderStatus.PENDING_PAYMENT:
                bad += 1
                continue
            order.status = ArtworkOrderStatus.CANCELLED
            order.cancelled_at = timezone.now()
            order.save(update_fields=["status", "cancelled_at", "updated_at"])
            if order.artwork.status == _AS.RESERVED:
                order.artwork.status = _AS.AVAILABLE
                order.artwork.save(update_fields=["status", "updated_at"])
            send_best_effort(sale_notifications.send_sale_cancelled, order)
            ok += 1
        if bad:
            self.message_user(request, f"{bad} pedido(s) no estaban pendientes de pago.", messages.ERROR)
        if ok:
            self.message_user(request, f"{ok} reserva(s) liberada(s).", messages.SUCCESS)


ArtworkAdmin.inlines = [*ArtworkAdmin.inlines, ArtworkOrderInline]
