"""Stripe one-off payment operations for artwork orders.

Owned by the `artworks` domain: creates `mode="payment"` Checkout Sessions,
verifies sessions (paid backstop), and issues refunds for the double-sale
backstop. Subscription-mode Stripe operations stay in
`subscriptions/services/stripe_client.py`.
"""

from decimal import Decimal

import stripe

import core.stripe  # noqa: F401  — initializes the Stripe SDK on import


def create_artwork_checkout_session(
    amount, currency, customer_email, metadata, success_url, cancel_url, expires_at, product_name="Obra de arte"
):
    """Create a one-off payment Checkout Session for an artwork order.

    Uses inline `price_data` (no Stripe Product/Price objects). `customer_email`
    prefills and locks the buyer email in Checkout. `expires_at` is a datetime
    (converted to epoch) or an epoch int.
    """
    if hasattr(expires_at, "timestamp"):
        expires_epoch = int(expires_at.timestamp())
    else:
        expires_epoch = int(expires_at)
    return stripe.checkout.Session.create(
        mode="payment",
        line_items=[
            {
                "price_data": {
                    "currency": currency.lower(),
                    "unit_amount": int(Decimal(amount) * 100),
                    "product_data": {"name": product_name},
                },
                "quantity": 1,
            }
        ],
        customer_email=customer_email,
        expires_at=expires_epoch,
        metadata=metadata,
        success_url=success_url,
        cancel_url=cancel_url,
    )


def retrieve_checkout_session(session_id):
    """Retrieve a Checkout Session by id (paid verification backstop)."""
    return stripe.checkout.Session.retrieve(session_id)


def create_refund(payment_intent_id):
    """Create a full refund for a payment intent (double-sale backstop)."""
    return stripe.Refund.create(payment_intent=payment_intent_id)
