from datetime import datetime, timezone as dt_timezone

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from core.models import TimeStampedModel
from solo.models import SingletonModel

from subscriptions.services.stripe_compat import sget, to_plain_dict


def epoch_to_datetime(ts):
    """Convert a Stripe unix timestamp to an aware datetime (UTC), or None."""
    if not ts:
        return None
    return datetime.fromtimestamp(ts, tz=dt_timezone.utc)


def map_stripe_status(stripe_status, cancel_at_period_end):
    """Map a Stripe subscription status onto ArtistSubscription.Status.

    A `canceled` status wins over `cancel_at_period_end` (the actual period
    ended). Otherwise a subscription scheduled for cancellation maps to
    CANCELING so the artist stays visible until the end of the paid period.
    """
    if stripe_status == "canceled":
        return ArtistSubscription.Status.CANCELED
    if cancel_at_period_end:
        return ArtistSubscription.Status.CANCELING
    mapping = {
        "active": ArtistSubscription.Status.ACTIVE,
        "trialing": ArtistSubscription.Status.ACTIVE,
        "past_due": ArtistSubscription.Status.PAST_DUE,
        "unpaid": ArtistSubscription.Status.PAST_DUE,
        "incomplete_expired": ArtistSubscription.Status.CANCELED,
        "incomplete": ArtistSubscription.Status.PENDING,
        "paused": ArtistSubscription.Status.PENDING,
    }
    return mapping.get(stripe_status, ArtistSubscription.Status.PENDING)


class BillingPlan(SingletonModel):
    """Single, admin-editable subscription plan (one Stripe price)."""

    name = models.CharField(
        max_length=100,
        default="Membresía Enredarte",
        verbose_name=_("Nombre del plan"),
        help_text=_("Nombre mostrado en el admin. Solo informativo."),
    )
    amount = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0,
        verbose_name=_("Monto"),
        help_text=_("Monto a cobrar por período. Debe ser mayor que 0."),
    )
    currency = models.CharField(
        max_length=3,
        choices=[("MXN", "MXN"), ("USD", "USD")],
        default="MXN",
        verbose_name=_("Moneda"),
        help_text=_("Moneda del precio. Solo MXN y USD."),
    )
    interval = models.CharField(
        max_length=10,
        choices=[("month", _("Mensual"))],
        default="month",
        verbose_name=_("Periodicidad"),
        help_text=_("Intervalo de facturación. Actualmente solo mensual."),
    )
    stripe_product_id = models.CharField(
        max_length=100,
        blank=True,
        default="",
        verbose_name=_("ID de producto en Stripe"),
        help_text=_("Identificador `prod_xxx` gestionado automáticamente. No editar manualmente."),
    )
    stripe_price_id = models.CharField(
        max_length=100,
        blank=True,
        default="",
        verbose_name=_("ID de precio en Stripe"),
        help_text=_("Identificador `price_xxx` gestionado automáticamente. No editar manualmente."),
    )
    last_synced_stripe_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Última sincronización con Stripe"),
        help_text=_("Última vez que se creó o archivó un precio en Stripe desde el admin."),
    )
    grace_period_days = models.PositiveIntegerField(
        default=3,
        verbose_name=_("Período de gracia (días)"),
        help_text=_("Días que un artista con pago fallido sigue visible en el sitio público."),
    )
    is_active_for_new_signups = models.BooleanField(
        default=True,
        verbose_name=_("Aceptar nuevas suscripciones"),
        help_text=_("Desactiva para pausar la generación de nuevos links de pago."),
    )

    class Meta:
        verbose_name = _("Plan de suscripción")
        verbose_name_plural = _("Planes de suscripción")

    def __str__(self):
        return self.name


class BillingPlanPriceHistory(models.Model):
    """Append-only audit of every price change."""

    billing_plan = models.ForeignKey(
        BillingPlan,
        on_delete=models.CASCADE,
        related_name="history",
        verbose_name=_("Plan de suscripción"),
        help_text=_("Plan al que pertenece este cambio de precio."),
    )
    old_stripe_price_id = models.CharField(
        max_length=100,
        blank=True,
        default="",
        verbose_name=_("ID de precio anterior"),
        help_text=_("Identificador `price_xxx` anterior. Vacío en la primera creación."),
    )
    new_stripe_price_id = models.CharField(
        max_length=100,
        verbose_name=_("ID de precio nuevo"),
        help_text=_("Identificador `price_xxx` recién creado en Stripe."),
    )
    amount = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        verbose_name=_("Monto"),
        help_text=_("Monto del nuevo precio."),
    )
    currency = models.CharField(
        max_length=3,
        verbose_name=_("Moneda"),
        help_text=_("Moneda del nuevo precio (MXN o USD)."),
    )
    interval = models.CharField(
        max_length=10,
        verbose_name=_("Periodicidad"),
        help_text=_("Intervalo del nuevo precio (actualmente solo mensual)."),
    )
    old_price_archived = models.BooleanField(
        default=True,
        verbose_name=_("Precio anterior archivado"),
        help_text=_("Si el precio anterior fue archivado (active=False) en Stripe."),
    )
    changed_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Fecha de cambio"),
        help_text=_("Momento en que se registró el cambio."),
    )
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name=_("Modificado por"),
        help_text=_("Usuario que realizó el cambio. Vacío si no hay usuario."),
    )

    class Meta:
        ordering = ["-changed_at"]
        verbose_name = _("Historial de precio")
        verbose_name_plural = _("Historial de precios")

    def __str__(self):
        dt = self.changed_at.strftime("%Y-%m-%d") if self.changed_at else "—"
        return f"{self.billing_plan} — {self.amount} {self.currency} / {self.interval} ({dt})"


class ArtistSubscription(TimeStampedModel):
    """1:1 mirror of the minimum Stripe state needed per artist."""

    class Status(models.TextChoices):
        PENDING = "pending", _("Pendiente de pago")
        ACTIVE = "active", _("Activa")
        PAST_DUE = "past_due", _("Pago fallido (en gracia)")
        CANCELING = "canceling", _("Cancelada, vigente hasta fin de período")
        CANCELED = "canceled", _("Cancelada definitivamente")

    artist = models.OneToOneField(
        "artworks.Artist",
        on_delete=models.CASCADE,
        related_name="subscription",
        verbose_name=_("Artista"),
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name=_("Estado"),
    )
    stripe_customer_id = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True,
        verbose_name=_("ID de cliente en Stripe"),
        help_text=_("Identificador `cus_xxx` asignado al generar el primer link de pago."),
    )
    stripe_subscription_id = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True,
        verbose_name=_("ID de suscripción en Stripe"),
        help_text=_("Identificador `sub_xxx` asignado tras el primer cobro."),
    )
    customer_email = models.EmailField(
        null=True,
        blank=True,
        verbose_name=_("Correo del cliente"),
    )
    current_period_end = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Fin del período actual"),
        help_text=_("Fecha en que termina el período ya pagado (según Stripe)."),
    )
    cancel_at_period_end = models.BooleanField(
        default=False,
        verbose_name=_("Cancelar al fin del período"),
        help_text=_("Verdadero cuando el artista pidió cancelar y sigue visible hasta el fin del período."),
    )
    signup_url = models.URLField(
        max_length=2000,
        blank=True,
        default="",
        verbose_name=_("Link de pago"),
        help_text=_("URL de la sesión de Checkout compartida con el artista."),
    )
    signup_url_expires_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("El link de pago expira"),
        help_text=_("Momento en que Stripe invalida la URL de Checkout."),
    )
    last_synced_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Última sincronización con Stripe"),
        help_text=_("Actualizado por webhooks o por la acción manual «Sincronizar desde Stripe»."),
    )
    raw_state = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Estado crudo de Stripe"),
        help_text=_("Último objeto de Stripe procesado, para depuración."),
    )

    class Meta:
        verbose_name = _("Suscripción de artista")
        verbose_name_plural = _("Suscripciones de artistas")

    def __str__(self):
        return f"{self.artist} — {self.get_status_display()}"

    def apply_stripe_payload(self, stripe_sub):
        """Mirror the fields of a Stripe subscription dict onto this row.

        Only fields derived from the new payload are touched; unrelated fields
        (e.g. `signup_url`) are left as-is. Persists immediately.
        """
        self.stripe_subscription_id = sget(stripe_sub, "id")
        cus = sget(stripe_sub, "customer")
        # Handle expanded customer object {"id": "cus_xxx", ...} vs string id
        if isinstance(cus, dict):
            cus = sget(cus, "id", cus) or cus
        self.stripe_customer_id = cus
        self.customer_email = sget(stripe_sub, "customer_email") or self.customer_email
        self.current_period_end = epoch_to_datetime(sget(stripe_sub, "current_period_end"))
        self.cancel_at_period_end = bool(sget(stripe_sub, "cancel_at_period_end"))
        self.status = map_stripe_status(sget(stripe_sub, "status"), self.cancel_at_period_end)
        self.raw_state = to_plain_dict(stripe_sub)
        self.last_synced_at = timezone.now()
        self.save(update_fields=[
            "status",
            "stripe_subscription_id",
            "stripe_customer_id",
            "customer_email",
            "current_period_end",
            "cancel_at_period_end",
            "raw_state",
            "last_synced_at",
            "updated_at",
        ])

    @classmethod
    def upsert_from_stripe(cls, stripe_sub):
        """Upsert a Stripe subscription dict onto the matching local row.

        Correlates by `stripe_subscription_id` first, then by
        `stripe_customer_id`. Returns the row, or None when no local
        `ArtistSubscription` matches (the event is logged but nothing changes).
        """
        sub_id = sget(stripe_sub, "id")
        cus_id = sget(stripe_sub, "customer")
        if isinstance(cus_id, dict):
            cus_id = sget(cus_id, "id", cus_id) or cus_id
        obj = (
            cls.objects.filter(stripe_subscription_id=sub_id).first()
            or cls.objects.filter(stripe_customer_id=cus_id).first()
        )
        if obj is None:
            return None
        obj.apply_stripe_payload(stripe_sub)
        return obj


class StripeEvent(models.Model):
    """Audit log of every webhook received from Stripe (idempotency source)."""

    event_id = models.CharField(
        max_length=120,
        unique=True,
        verbose_name=_("ID del evento"),
        help_text=_("`evt_xxx` tal como lo envía Stripe. Único: bloquea duplicados."),
    )
    event_type = models.CharField(
        max_length=80,
        verbose_name=_("Tipo de evento"),
    )
    received_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Recibido el"),
    )
    processed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Procesado el"),
        help_text=_("Relleno tras procesar el evento; vacío si falló."),
    )
    payload = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Carga útil"),
        help_text=_("Objeto del evento completo tal como lo envió Stripe."),
    )
    error = models.TextField(
        blank=True,
        default="",
        verbose_name=_("Error"),
        help_text=_("Mensaje de excepción si el procesamiento falló."),
    )

    class Meta:
        ordering = ["-received_at"]
        verbose_name = _("Evento de Stripe")
        verbose_name_plural = _("Eventos de Stripe")

    def __str__(self):
        return f"{self.event_type} ({self.event_id[:20]})"