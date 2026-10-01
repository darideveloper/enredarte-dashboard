"""Append-only financial ledger writes.

Every function here creates ``FinancialEntry`` rows from an economic event that
already happened elsewhere (artwork paid/refunded, Stripe invoice paid, cash
confirmation). Rows are never edited or deleted. Creation is idempotent: a
non-empty ``reference`` is checked first, and the partial unique constraint on
(``kind``, ``reference``) is the final guard inside a savepoint so a duplicate
never aborts the caller's transaction.
"""

import logging
from datetime import datetime
from decimal import Decimal

from django.db import IntegrityError, transaction
from django.utils import timezone

from finance.models import FinancialEntry

logger = logging.getLogger(__name__)

_CENTS = Decimal("100")
_Q2 = Decimal("0.01")


def _entry_date(value):
    """Return a date for a datetime/date/None value (project timezone)."""
    if value is None:
        return timezone.localdate()
    if isinstance(value, datetime):
        if timezone.is_naive(value):
            value = timezone.make_aware(value)
        return timezone.localdate(value)
    return value


def _create_entry(
    *,
    kind,
    amount,
    currency,
    occurred_on,
    artist=None,
    payment_method=None,
    order=None,
    subscription=None,
    reference="",
    note="",
):
    """Create one ledger row; return it, or the existing row / None on skip."""
    amount = Decimal(amount).quantize(_Q2)
    if amount == 0:
        return None
    if reference:
        existing = FinancialEntry.objects.filter(kind=kind, reference=reference).first()
        if existing is not None:
            return existing
    try:
        with transaction.atomic():
            return FinancialEntry.objects.create(
                kind=kind,
                amount=amount,
                currency=currency,
                occurred_on=_entry_date(occurred_on),
                artist=artist,
                payment_method=payment_method,
                order=order,
                subscription=subscription,
                reference=reference,
                note=note,
            )
    except IntegrityError:
        # Concurrent duplicate: the unique (kind, reference) guard won.
        return FinancialEntry.objects.filter(kind=kind, reference=reference).first()


def record_artwork_sale(order):
    """Create the +sale and (when applicable) −commission rows for a paid order.

    The artist's commission percentage is frozen at this moment: later edits to
    ``Artist.commission`` never change these rows.
    """
    artist = order.artwork.artist
    currency = (order.currency or "").upper()
    occurred_on = _entry_date(order.paid_at)
    base_ref = order.stripe_payment_intent_id or order.slug
    created = []

    sale = _create_entry(
        kind=FinancialEntry.Kind.ARTWORK_SALE,
        amount=order.amount,
        currency=currency,
        occurred_on=occurred_on,
        artist=artist,
        payment_method=FinancialEntry.PaymentMethod.STRIPE,
        order=order,
        reference=base_ref,
        note=f"Venta: {order.artwork}",
    )
    if sale is not None:
        created.append(sale)

    percentage = artist.commission or 0
    if percentage:
        commission = -(Decimal(order.amount) * Decimal(percentage) / Decimal("100"))
        entry = _create_entry(
            kind=FinancialEntry.Kind.ARTIST_COMMISSION,
            amount=commission,
            currency=currency,
            occurred_on=occurred_on,
            artist=artist,
            payment_method=FinancialEntry.PaymentMethod.STRIPE,
            order=order,
            reference=f"{base_ref}-commission",
            note=f"Comisión {percentage}%: {order.artwork}",
        )
        if entry is not None:
            created.append(entry)
    return created


def record_artwork_refund(order):
    """Reverse the order's recorded ledger entries so they net to zero.

    Each existing row for the order (sale and/or commission) gets an opposite
    row; nothing is created when the order has no recorded movement (the
    double-sale backstop refunds a charge that was never booked as a sale, so
    the charge/refund pair nets to zero and must not distort totals).
    """
    artist = order.artwork.artist
    currency = (order.currency or "").upper()
    occurred_on = _entry_date(order.cancelled_at)
    created = []

    originals = FinancialEntry.objects.filter(order=order).exclude(
        reference__endswith="-refund"
    )
    for original in originals.order_by("id"):
        entry = _create_entry(
            kind=original.kind,
            amount=-original.amount,
            currency=currency,
            occurred_on=occurred_on,
            artist=artist,
            payment_method=original.payment_method,
            order=order,
            reference=f"{original.reference}-refund",
            note=f"Reverso: {order.artwork}",
        )
        if entry is not None:
            created.append(entry)
    return created


def record_subscription_payment(
    *,
    artist,
    amount,
    currency,
    occurred_on=None,
    payment_method,
    subscription=None,
    reference="",
    note="",
):
    """Create a +subscription_payment row from an already-confirmed payment."""
    return _create_entry(
        kind=FinancialEntry.Kind.SUBSCRIPTION_PAYMENT,
        amount=amount,
        currency=currency,
        occurred_on=occurred_on,
        artist=artist,
        payment_method=payment_method,
        subscription=subscription,
        reference=reference,
        note=note,
    )


def record_cash_subscription_payment(subscription, paid_on=None):
    """Snapshot the current plan amount for a confirmed cash payment.

    Keyed by the artist and the resulting paid period so an exact duplicate
    confirm is suppressed, while each genuine monthly confirm still records.
    """
    from subscriptions.models import BillingPlan

    plan = BillingPlan.get_solo()
    occurred_on = paid_on or timezone.localdate()
    period_end = subscription.current_period_end
    period_key = period_end.date().isoformat() if period_end else occurred_on.isoformat()
    return record_subscription_payment(
        artist=subscription.artist,
        amount=plan.amount,
        currency=(plan.currency or "").upper(),
        occurred_on=occurred_on,
        payment_method=FinancialEntry.PaymentMethod.CASH,
        subscription=subscription,
        reference=f"cash:{subscription.artist_id}:{period_key}",
        note="Pago en efectivo",
    )


def cents_to_amount(value):
    """Convert a Stripe integer minor-unit amount into a major-unit Decimal."""
    return (Decimal(value or 0) / _CENTS).quantize(_Q2)
