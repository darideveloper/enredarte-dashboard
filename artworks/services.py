"""Shared artwork-order transitions (views, webhooks, commands)."""

import logging

from django.db import transaction
from django.utils import timezone

from artworks.models import Artwork, ArtworkOrder, ArtworkOrderStatus, ArtworkStatus

logger = logging.getLogger(__name__)


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


def _reconciled_buyer(session, sget, order):
    """Extract (payment_intent, email, name) from a Checkout Session.

    Mirrors the webhook reader: works for plain dicts and StripeObjects.
    """
    pi = sget(session, "payment_intent") or ""
    if isinstance(pi, dict):
        pi = pi.get("id", "")
    details = sget(session, "customer_details") or {}
    if not isinstance(details, dict):
        details = {}
    email = details.get("email", "") or sget(session, "customer_email") or ""
    name = details.get("name", "") or ""
    return str(pi or ""), str(email or ""), str(name or "")


def _cancel_reconciled(order_id):
    """Cancel a stale order inside row locks after re-verifying PENDING_PAYMENT."""
    with transaction.atomic():
        try:
            order = ArtworkOrder.objects.select_for_update().get(pk=order_id)
        except ArtworkOrder.DoesNotExist:
            return False
        return cancel_order(order)


def _apply_reconciled_paid(order_id, session):
    """Paid-transition inside row locks, with the double-sale refund backstop."""
    from subscriptions.services import stripe_client
    from subscriptions.services.stripe_compat import sget

    with transaction.atomic():
        try:
            order = ArtworkOrder.objects.select_for_update().get(pk=order_id)
        except ArtworkOrder.DoesNotExist:
            return False
        if order.status != ArtworkOrderStatus.PENDING_PAYMENT:
            return False
        artwork = Artwork.objects.select_for_update().get(pk=order.artwork_id)
        pi, email, name = _reconciled_buyer(session, sget, order)
        if artwork.status not in (ArtworkStatus.RESERVED, ArtworkStatus.AVAILABLE):
            order.status = ArtworkOrderStatus.REFUNDED
            order.stripe_payment_intent_id = pi or order.stripe_payment_intent_id
            order.save(update_fields=["status", "stripe_payment_intent_id", "updated_at"])
            logger.warning("reconcile double-sale order=%s refunding pi=%s", order.slug, pi)
            stripe_client.create_refund(pi)
            return True
        # Point the transition at our locked row so it cannot drift mid-flight.
        order.artwork = artwork
        return apply_paid_transition(order, pi, email or order.buyer_email, name)


def reconcile_stale_reservations(artwork):
    """Reconcile stale RESERVED holds against Stripe (lazy, zero-infra).

    Two-phase contract: phase 1 reads stale orders and calls Stripe with no
    DB lock held; phase 2 re-verifies inside ``select_for_update`` before
    mutating (see ``_cancel_reconciled`` / ``_apply_reconciled_paid``).

    Returns ``"released"`` (freed >= 1 hold), ``"sold"`` (verified paid),
    ``"kept"`` (live, open/unpaid, unverifiable, or concurrently-resolved
    hold — callers always re-read the row, so behavior stays correct), or
    ``"noop"`` (nothing stale to reconcile — zero Stripe calls).
    """
    from subscriptions.services import stripe_client
    from subscriptions.services.stripe_compat import sget

    if artwork.status != ArtworkStatus.RESERVED:
        return "noop"
    stale = list(
        ArtworkOrder.objects.filter(
            artwork_id=artwork.pk,
            status=ArtworkOrderStatus.PENDING_PAYMENT,
            session_expires_at__lt=timezone.now(),
        ).order_by("-created_at")
    )
    if not stale:
        return "noop"
    outcome = "kept"
    for order in stale:
        try:
            session = stripe_client.retrieve_checkout_session(
                order.stripe_checkout_session_id
            )
        except Exception:
            logger.warning("reconcile stale order=%s stripe retrieve failed", order.slug)
            continue
        if (sget(session, "payment_status") or "") == "paid":
            if _apply_reconciled_paid(order.pk, session):
                return "sold"
            continue
        if (sget(session, "status") or "") == "expired":
            if _cancel_reconciled(order.pk):
                outcome = "released"
            continue
        # Still open + unpaid (async settling) or unknown shape → keep.
        logger.info("reconcile stale order=%s holding (unpaid/open)", order.slug)
    return outcome
