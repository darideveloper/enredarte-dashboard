"""Backfill `artwork_sale` (+ `artist_commission`) entries for paid orders.

Pre-existing subscription payments (cash and Stripe) are NOT backfilled: those
were stored only as current state and cannot be reconstructed. Artwork sales
can, so they are seeded here using each artist's *current* commission
percentage (the historical value is unrecoverable). Idempotent and reversible:
forward uses `ignore_conflicts`, reverse deletes the order-linked ledger rows.
"""

from decimal import Decimal

from django.db import migrations
from django.utils import timezone

PAID_STATUSES = ("paid_pending_data", "data_complete", "shipped", "delivered")


def _date_of(value):
    if value is None:
        return timezone.localdate()
    if timezone.is_naive(value):
        value = timezone.make_aware(value)
    return timezone.localdate(value)


def backfill(apps, schema_editor):
    FinancialEntry = apps.get_model("finance", "FinancialEntry")
    ArtworkOrder = apps.get_model("artworks", "ArtworkOrder")

    entries = []
    orders = (
        ArtworkOrder.objects.filter(paid_at__isnull=False, status__in=PAID_STATUSES)
        .select_related("artwork__artist")
    )
    for order in orders:
        artist = order.artwork.artist
        currency = (order.currency or "").upper()
        occurred_on = _date_of(order.paid_at)
        base_ref = order.stripe_payment_intent_id or order.slug
        entries.append(
            FinancialEntry(
                kind="artwork_sale",
                amount=Decimal(order.amount).quantize(Decimal("0.01")),
                currency=currency,
                occurred_on=occurred_on,
                artist=artist,
                payment_method="stripe",
                order=order,
                reference=base_ref,
                note=f"Venta (histórico): {order.artwork}",
            )
        )
        percentage = artist.commission or 0
        if percentage:
            commission = -(
                Decimal(order.amount) * Decimal(percentage) / Decimal("100")
            ).quantize(Decimal("0.01"))
            entries.append(
                FinancialEntry(
                    kind="artist_commission",
                    amount=commission,
                    currency=currency,
                    occurred_on=occurred_on,
                    artist=artist,
                    payment_method="stripe",
                    order=order,
                    reference=f"{base_ref}-commission",
                    note=f"Comisión {percentage}% (histórico): {order.artwork}",
                )
            )

    # ponytail: ignore_conflicts skips rows already present (unique kind+reference).
    FinancialEntry.objects.bulk_create(entries, ignore_conflicts=True)


def unbackfill(apps, schema_editor):
    FinancialEntry = apps.get_model("finance", "FinancialEntry")
    FinancialEntry.objects.filter(
        kind__in=("artwork_sale", "artist_commission"), order__isnull=False
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("finance", "0001_initial"),
        ("artworks", "0013_artist_commission"),
    ]

    operations = [
        migrations.RunPython(backfill, unbackfill),
    ]
