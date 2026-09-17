"""Shared artwork-order transitions (views, webhooks, commands)."""

from django.utils import timezone

from artworks.models import ArtworkOrderStatus, ArtworkStatus


def apply_paid_transition(order, payment_intent_id="", buyer_email="", buyer_name=""):
    """Apply idempotent paid-transition; return True if transitioned."""
    if order.status != ArtworkOrderStatus.PENDING_PAYMENT:
        return False
    order.stripe_payment_intent_id = payment_intent_id or order.stripe_payment_intent_id
    if buyer_email:
        order.buyer_email = buyer_email.strip().lower()
    if buyer_name:
        order.buyer_name = buyer_name
    order.paid_at = timezone.now()
    order.status = ArtworkOrderStatus.PAID_PENDING_DATA
    order.save(
        update_fields=[
            "stripe_payment_intent_id",
            "buyer_email",
            "buyer_name",
            "paid_at",
            "status",
            "updated_at",
        ]
    )
    artwork = order.artwork
    if artwork.status != ArtworkStatus.SOLD:
        artwork.status = ArtworkStatus.SOLD
        artwork.save(update_fields=["status", "updated_at"])
    return True


def artwork_reserved_by(order):
    """True when the artwork is still reservable by this order."""
    return order.artwork.status in (ArtworkStatus.RESERVED, ArtworkStatus.AVAILABLE)


def cancel_order(order):
    """Cancel a pending order and release the artwork; return True if changed."""
    if order.status != ArtworkOrderStatus.PENDING_PAYMENT:
        return False
    order.status = ArtworkOrderStatus.CANCELLED
    order.cancelled_at = timezone.now()
    order.save(update_fields=["status", "cancelled_at", "updated_at"])
    artwork = order.artwork
    if artwork.status == ArtworkStatus.RESERVED:
        artwork.status = ArtworkStatus.AVAILABLE
        artwork.save(update_fields=["status", "updated_at"])
    return True
