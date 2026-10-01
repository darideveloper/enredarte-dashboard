from django.db import models
from django.db.models import Q

from core.models import TimeStampedModel


class FinancialEntry(TimeStampedModel):
    """Append-only ledger of every money movement (income and expenses).

    One row per economic event. `amount` is signed: positive for income
    (artwork sales, subscription payments) and negative for expenses (artist
    commissions). Rows are created automatically by the flows that own the
    event; operators only toggle `reconciled`.
    """

    class Kind(models.TextChoices):
        ARTWORK_SALE = "artwork_sale", "Venta de obra"
        ARTIST_COMMISSION = "artist_commission", "Comisión de artista"
        SUBSCRIPTION_PAYMENT = "subscription_payment", "Pago de suscripción"

    class Currency(models.TextChoices):
        MXN = "MXN", "MXN"
        USD = "USD", "USD"

    class PaymentMethod(models.TextChoices):
        CASH = "cash", "Efectivo"
        STRIPE = "stripe", "En línea"

    occurred_on = models.DateField(
        verbose_name="Fecha",
        help_text="Fecha del movimiento; determina el mes al que pertenece.",
        db_index=True,
    )
    kind = models.CharField(
        max_length=32,
        choices=Kind.choices,
        verbose_name="Tipo",
        help_text="Naturaleza del movimiento: venta, comisión o pago de suscripción.",
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Monto",
        help_text="Monto con signo: positivo para ingresos, negativo para gastos (comisiones).",
    )
    currency = models.CharField(
        max_length=3,
        choices=Currency.choices,
        verbose_name="Moneda",
        help_text="Moneda del movimiento. Los totales se agrupan por moneda.",
    )
    artist = models.ForeignKey(
        "artworks.Artist",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="financial_entries",
        verbose_name="Artista",
        help_text="Artista relacionado (venta, comisión o suscripción).",
    )
    payment_method = models.CharField(
        max_length=10,
        choices=PaymentMethod.choices,
        null=True,
        blank=True,
        verbose_name="Método de pago",
        help_text="En línea (Stripe) o efectivo. Vacío para movimientos sin método.",
    )
    order = models.ForeignKey(
        "artworks.ArtworkOrder",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="financial_entries",
        verbose_name="Pedido de obra",
        help_text="Pedido que originó el movimiento, cuando aplica.",
    )
    subscription = models.ForeignKey(
        "subscriptions.ArtistSubscription",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="financial_entries",
        verbose_name="Suscripción",
        help_text="Suscripción que originó el movimiento, cuando aplica.",
    )
    reference = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Referencia",
        help_text="Clave del evento de origen; evita registrar el mismo movimiento dos veces.",
    )
    note = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Nota",
        help_text="Descripción breve del movimiento.",
    )
    reconciled = models.BooleanField(
        default=False,
        verbose_name="Conciliado",
        help_text="Marca manual: el movimiento ya fue validado (o la comisión ya se pagó al artista).",
    )

    class Meta:
        ordering = ["-occurred_on", "-id"]
        verbose_name = "Movimiento"
        verbose_name_plural = "Movimientos"
        constraints = [
            models.UniqueConstraint(
                fields=["kind", "reference"],
                condition=~Q(reference=""),
                name="unique_finance_kind_reference",
            )
        ]

    def __str__(self):
        return f"{self.occurred_on} · {self.get_kind_display()} · {self.amount} {self.currency}"
