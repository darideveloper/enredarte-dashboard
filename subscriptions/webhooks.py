"""Stripe webhook receiver.

Mounted at `/webhooks/stripe/` OUTSIDE the admin (no authentication); the
security boundary is the `Stripe-Signature` header verified here. Every event
is recorded in `StripeEvent` (unique `event_id`) for idempotency and audit;
handled events run inside a single transaction so `ArtistSubscription` and
`Artist.is_active` move together or not at all.
"""

import logging

import stripe
from django.conf import settings
from django.db import IntegrityError, transaction
from django.http import HttpResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from subscriptions.models import ArtistSubscription, StripeEvent, epoch_to_datetime
from subscriptions.services.stripe_compat import sget, to_plain_dict
from subscriptions.services.subscription_state import compute_is_active

logger = logging.getLogger(__name__)


def _sync_artist(subscription):
    """Persist `compute_is_active(subscription)` onto the subscription's artist."""
    subscription.artist.is_active = compute_is_active(subscription)
    subscription.artist.save(update_fields=["is_active", "updated_at"])


def _find_subscription(customer_id, subscription_id):
    """Correlate a Stripe event to a local row by sub id first, then customer."""
    if subscription_id:
        obj = ArtistSubscription.objects.filter(stripe_subscription_id=subscription_id).first()
        if obj:
            return obj
    if customer_id:
        return ArtistSubscription.objects.filter(stripe_customer_id=customer_id).first()
    return None


def _invoice_period_end(invoice):
    """New period end carried by the first line of an invoice."""
    lines = (invoice.get("lines") or {}).get("data") or []
    if not lines:
        return None
    period = lines[0].get("period") or {}
    return epoch_to_datetime(period.get("end"))


def _handle_checkout_completed(event):
    session = event["data"]["object"]
    artist_id = (session.get("metadata") or {}).get("artist_id")
    if not artist_id:
        return
    sub = ArtistSubscription.objects.filter(artist_id=artist_id).first()
    if sub is None:
        return
    changed = False
    if session.get("customer") and not sub.stripe_customer_id:
        sub.stripe_customer_id = session["customer"]
        changed = True
    if session.get("subscription") and not sub.stripe_subscription_id:
        sub.stripe_subscription_id = session["subscription"]
        changed = True
    if changed:
        sub.last_synced_at = timezone.now()
        sub.save(
            update_fields=[
                "stripe_customer_id",
                "stripe_subscription_id",
                "last_synced_at",
                "updated_at",
            ]
        )
    _sync_artist(sub)


def _handle_subscription_created(event):
    stripe_sub = event["data"]["object"]
    sub = ArtistSubscription.upsert_from_stripe(stripe_sub)
    if sub is None:
        return
    sub.signup_url = ""
    sub.signup_url_expires_at = None
    sub.save(update_fields=["signup_url", "signup_url_expires_at", "updated_at"])
    _sync_artist(sub)


def _handle_subscription_updated(event):
    stripe_sub = event["data"]["object"]
    sub = ArtistSubscription.upsert_from_stripe(stripe_sub)
    if sub is None:
        return
    _sync_artist(sub)


def _handle_subscription_deleted(event):
    stripe_sub = event["data"]["object"]
    sub = ArtistSubscription.upsert_from_stripe(stripe_sub)
    if sub is None:
        return
    _sync_artist(sub)


def _handle_invoice_payment_succeeded(event):
    invoice = event["data"]["object"]
    sub = _find_subscription(invoice.get("customer"), invoice.get("subscription"))
    if sub is None:
        return
    sub.status = ArtistSubscription.Status.ACTIVE
    sub.cancel_at_period_end = False
    period_end = _invoice_period_end(invoice)
    if period_end is not None:
        sub.current_period_end = period_end
    sub.raw_state = to_plain_dict(invoice)
    sub.last_synced_at = timezone.now()
    # Only update current_period_end if invoice had a period (guard empty lines)
    update_fields = ["status", "cancel_at_period_end", "raw_state", "last_synced_at", "updated_at"]
    if period_end is not None:
        update_fields.insert(2, "current_period_end")
        sub.save(update_fields=update_fields)
    else:
        sub.save(
            update_fields=[
                "status",
                "cancel_at_period_end",
                "raw_state",
                "last_synced_at",
                "updated_at",
            ]
        )
    _sync_artist(sub)


def _handle_invoice_payment_failed(event):
    invoice = event["data"]["object"]
    sub = _find_subscription(invoice.get("customer"), invoice.get("subscription"))
    if sub is None:
        return
    sub.status = ArtistSubscription.Status.PAST_DUE
    sub.raw_state = to_plain_dict(invoice)
    sub.last_synced_at = timezone.now()
    sub.save(
        update_fields=["status", "raw_state", "last_synced_at", "updated_at"]
    )
    _sync_artist(sub)


def _handle_checkout_expired(event):
    session = event["data"]["object"]
    meta = sget(session, "metadata") or {}
    artist_id = sget(meta, "artist_id") if isinstance(meta, dict) else None
    if not artist_id:
        return
    sub = ArtistSubscription.objects.filter(artist_id=artist_id).first()
    if sub is None or not sub.signup_url:
        return
    # Clear if stored url matches session url or fallback by artist_id match
    session_url = sget(session, "url") or ""
    if session_url and sub.signup_url != session_url:
        # URL mismatch but artist_id matches — still clear per spec fallback
        pass
    sub.signup_url = ""
    sub.signup_url_expires_at = None
    sub.last_synced_at = timezone.now()
    sub.save(update_fields=["signup_url", "signup_url_expires_at", "last_synced_at", "updated_at"])
    logger.info("checkout expired artist=%s cleared signup_url", artist_id)
    # Status stays as-is (typically pending), no change


HANDLERS = {
    "checkout.session.completed": _handle_checkout_completed,
    "checkout.session.expired": _handle_checkout_expired,
    "customer.subscription.created": _handle_subscription_created,
    "customer.subscription.updated": _handle_subscription_updated,
    "customer.subscription.deleted": _handle_subscription_deleted,
    "invoice.payment_succeeded": _handle_invoice_payment_succeeded,
    "invoice.payment_failed": _handle_invoice_payment_failed,
}


@csrf_exempt
def stripe_webhook(request):
    """Signed, idempotent Stripe webhook endpoint."""
    if request.method != "POST":
        return HttpResponse(status=405)

    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
    if not sig_header:
        logger.warning("webhook missing Stripe-Signature header")
        return HttpResponse(status=400)

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except (ValueError, stripe.error.SignatureVerificationError) as e:
        logger.warning("webhook invalid signature: %s", e)
        return HttpResponse(status=400)

    # Stripe v15: use for_json=True to handle Decimal; fallback for 11.x
    try:
        event_dict = event.to_dict(for_json=True)
    except TypeError:
        event_dict = event.to_dict()
    event_dict = to_plain_dict(event_dict)

    try:
        # One transaction wraps the StripeEvent INSERT and the handler so they
        # commit together. The unique index is still the idempotency lock: a
        # concurrent duplicate delivery raises IntegrityError and returns 200
        # without running the handler. On handler crash, the whole block
        # (including the INSERT) rolls back so Stripe's retry sees no row and
        # re-runs the handler as a fresh attempt.
        with transaction.atomic():
            record = StripeEvent.objects.create(
                event_id=event_dict["id"],
                event_type=event_dict["type"],
                payload=event_dict,
            )
            handler = HANDLERS.get(event_dict["type"])
            if handler:
                handler(event_dict)
            record.processed_at = timezone.now()
            record.save(update_fields=["processed_at"])
    except IntegrityError:
        # Duplicate delivery of the same event_id: already processed, no-op.
        logger.info("webhook duplicate %s %s", event_dict.get("type"), event_dict.get("id"))
        return HttpResponse(status=200)
    except Exception:
        logger.exception("webhook %s failed", event_dict.get("id"))
        return HttpResponse(status=500)

    logger.info("webhook %s %s", event_dict.get("type"), event_dict.get("id"))
    return HttpResponse(status=200)