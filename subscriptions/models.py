from datetime import datetime, timezone as dt_timezone

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from core.models import TimeStampedModel
from solo.models import SingletonModel


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
    stripe_price_id = models.CharField(
        max_length=100,
        blank=True,
        default="",
        verbose_name=_("ID de precio en Stripe"),
        help_text=_("Pega el `price_xxx` del producto creado en el Dashboard de Stripe."),
    )
    currency = models.CharField(
        max_length=3,
        default="MXN",
        verbose_name=_("Moneda (ISO 4217)"),
        help_text=_("Código ISO 4217 de tres letras, p. ej. MXN."),
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
        self.stripe_subscription_id = stripe_sub.get("id")
        self.stripe_customer_id = stripe_sub.get("customer")
        self.customer_email = stripe_sub.get("customer_email") or self.customer_email
        self.current_period_end = epoch_to_datetime(stripe_sub.get("current_period_end"))
        self.cancel_at_period_end = bool(stripe_sub.get("cancel_at_period_end"))
        self.status = map_stripe_status(stripe_sub.get("status"), self.cancel_at_period_end)
        self.raw_state = stripe_sub
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
        sub_id = stripe_sub.get("id")
        cus_id = stripe_sub.get("customer")
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