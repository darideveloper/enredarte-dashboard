"""Artwork-sale webhook logic, delegated from the signed Stripe envelope.

The envelope (`subscriptions/webhooks.py`) owns signature verification, the
`StripeEvent` idempotency insert, and the single atomic block. These pure
functions take the event and act on the `ArtworkOrder`; they return `False`
when the session is not an artwork-order session so the envelope falls through
to its subscription handlers.
"""

import logging

from django.db import transaction

from artworks import sale_notifications, stripe_orders
from artworks.models import ArtworkOrder, ArtworkOrderStatus
from artworks.services import apply_paid_transition, artwork_reserved_by, cancel_order
from core.mail_utils import send_best_effort
from core.stripe_compat import sget

logger = logging.getLogger(__name__)


def _session_meta(session):
    meta = sget(session, "metadata") or {}
    if not isinstance(meta, dict):
        return {}
    return meta


def _find_artwork_order(session):
    meta = _session_meta(session)
    if meta.get("kind") != "artwork_order":
        return None, meta
    slug = meta.get("order")
    if not slug:
        return None, meta
    order = (
        ArtworkOrder.objects.select_related("artwork").filter(slug=slug).first()
    )
    return order, meta


def _session_buyer(session):
    pi = sget(session, "payment_intent") or ""
    if isinstance(pi, dict):
        pi = pi.get("id", "")
    details = sget(session, "customer_details") or {}
    if not isinstance(details, dict):
        details = {}
    email = details.get("email", "") if isinstance(details, dict) else ""
    name = details.get("name", "") if isinstance(details, dict) else ""
    if not email:
        email = sget(session, "customer_email") or ""
    return str(pi or ""), str(email or ""), str(name or "")


def _apply_artwork_paid(order, session):
    """Paid-transition with double-sale refund backstop."""
    if order.status != ArtworkOrderStatus.PENDING_PAYMENT:
        return
    pi, email, name = _session_buyer(session)
    if not artwork_reserved_by(order):
        order.status = ArtworkOrderStatus.REFUNDED
        order.stripe_payment_intent_id = pi or order.stripe_payment_intent_id
        order.save(update_fields=["status", "stripe_payment_intent_id", "updated_at"])
        logger.warning("artwork double-sale order=%s refunding pi=%s", order.slug, pi)
        refund = stripe_orders.create_refund(pi)
        refund_id = (
            getattr(refund, "id", "") if not isinstance(refund, dict) else refund.get("id", "")
        )
        transaction.on_commit(
            lambda o=order, rid=refund_id: send_best_effort(
                sale_notifications.send_sale_refunded, o, refund_id=rid
            )
        )
        return
    if apply_paid_transition(order, pi, email or order.buyer_email, name):
        transaction.on_commit(
            lambda o=order: send_best_effort(sale_notifications.send_sale_paid, o)
        )


def handle_checkout_completed(event):
    """Handle a `checkout.session.completed` event; return True if artwork."""
    session = event["data"]["object"]
    order, _ = _find_artwork_order(session)
    if order is None:
        return False
    if (sget(session, "payment_status") or "") != "paid":
        return True
    _apply_artwork_paid(order, session)
    return True


def handle_checkout_expired(event):
    """Handle a `checkout.session.expired` event; return True if artwork."""
    session = event["data"]["object"]
    order, _ = _find_artwork_order(session)
    if order is None:
        return False
    if cancel_order(order):
        transaction.on_commit(
            lambda o=order: send_best_effort(sale_notifications.send_sale_cancelled, o)
        )
    return True


def handle_async_payment_succeeded(event):
    """Handle `checkout.session.async_payment_succeeded`; return True if artwork."""
    session = event["data"]["object"]
    order, _ = _find_artwork_order(session)
    if order is None:
        return False
    _apply_artwork_paid(order, session)
    return True


def handle_async_payment_failed(event):
    """Handle `checkout.session.async_payment_failed`; return True if artwork."""
    session = event["data"]["object"]
    order, _ = _find_artwork_order(session)
    if order is None:
        return False
    if cancel_order(order):
        transaction.on_commit(
            lambda o=order: send_best_effort(sale_notifications.send_sale_cancelled, o)
        )
    return True
