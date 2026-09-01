"""Thin wrapper around the Stripe SDK.

Only this module imports the `stripe` package directly; webhooks and views
consume the small surface exposed here. The SDK is configured once on import
using the project settings.
"""

import stripe
from decimal import Decimal

from django.conf import settings
from django.utils import timezone

if settings.STRIPE_SECRET_KEY:
    stripe.api_key = settings.STRIPE_SECRET_KEY
if settings.STRIPE_API_VERSION:
    stripe.api_version = settings.STRIPE_API_VERSION


def create_customer(email):
    """Create a Stripe Customer for an artist and return the customer object."""
    return stripe.Customer.create(email=email)


def create_checkout_session(customer_id, metadata, price_id):
    """Create a subscription-mode Checkout Session and return the session object.

    `metadata` carries `artist_id` so webhooks can correlate the result back
    to our `Artist` row. Success/cancel landing URLs come from settings.
    """
    return stripe.checkout.Session.create(
        customer=customer_id,
        mode="subscription",
        line_items=[{"price": price_id, "quantity": 1}],
        metadata=metadata,
        success_url=settings.STRIPE_SUCCESS_URL,
        cancel_url=settings.STRIPE_CANCEL_URL,
    )


def expire_or_reuse_session(url, expires_at):
    """Return the existing Checkout URL while still valid, otherwise None.

    Used by the regenerate-link flow: an operator regenerates only when the
    previous URL has expired or already been used.
    """
    if url and expires_at and expires_at > timezone.now():
        return url
    return None


def create_billing_portal_session(customer_id):
    """Create a Stripe Customer Portal session and return the session object.

    The `return_url` is a neutral landing page so an artist who just cancelled
    in the portal does not land on the "subscription active" success text.
    """
    return stripe.billing_portal.Session.create(
        customer=customer_id,
        return_url=settings.STRIPE_PORTAL_RETURN_URL,
    )


def fetch_subscription(sub_id):
    """Return a Stripe subscription object by id.

    Part of the public client surface (used by the sync flow when an id is
    known; also the building block for a future `subscriptions/reconcile`
    management command).
    """
    return stripe.Subscription.retrieve(sub_id)


def fetch_customer(cus_id):
    """Return a Stripe customer object by id."""
    return stripe.Customer.retrieve(cus_id)


def list_subscriptions(customer_id, limit=1):
    """Return the most recent subscriptions for a Stripe customer.

    Used by the manual sync salvavidas: listing by customer stays robust when
    the locally stored `stripe_subscription_id` is stale or was deleted.
    """
    return stripe.Subscription.list(customer=customer_id, limit=limit)


def get_or_create_product(name: str, existing_id: str = ""):
    """Return a Stripe Product, reusing existing_id when present."""
    if existing_id:
        return stripe.Product.retrieve(existing_id)
    return stripe.Product.create(name=name)


def create_price(product_id, amount_decimal, currency, interval):
    """Create a Stripe Price for the given product/amount/currency/interval."""
    return stripe.Price.create(
        product=product_id,
        unit_amount=int(Decimal(amount_decimal) * 100),
        currency=currency.lower(),
        recurring={"interval": interval},
    )


def archive_price(price_id):
    """Archive a Stripe Price (set active=False)."""
    return stripe.Price.modify(price_id, active=False)


def retrieve_price(price_id):
    """Retrieve a Stripe Price by id."""
    return stripe.Price.retrieve(price_id)


def set_product_default_price(product_id, price_id):
    """Set the product's default_price to price_id."""
    return stripe.Product.modify(product_id, default_price=price_id)