"""Single Stripe SDK initializer for every money-path module.

Imported (for its side effects) by the subscription client
(`subscriptions/services/stripe_client.py`) and the artwork-sale client
(`artworks/stripe_orders.py`), so any path that calls the Stripe SDK —
web request, webhook, or management command — is authenticated before the
first API call, even when no subscription module is otherwise imported.
"""

import logging
import os

import stripe
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger(__name__)

if settings.STRIPE_SECRET_KEY:
    stripe.api_key = settings.STRIPE_SECRET_KEY
if settings.STRIPE_API_VERSION:
    stripe.api_version = settings.STRIPE_API_VERSION

# Fail fast outside dev when the app cannot talk to Stripe. Mirrors the boot
# gate in `subscriptions/apps.py:ready`, but here it protects every entrypoint
# that imports the SDK directly (including artwork-only commands).
if os.getenv("ENV", "dev") != "dev":
    if not settings.STRIPE_SECRET_KEY:
        raise ImproperlyConfigured(
            "STRIPE_SECRET_KEY missing: Stripe calls would be unauthenticated"
        )
    if not settings.STRIPE_WEBHOOK_SECRET.startswith("whsec_"):
        raise ImproperlyConfigured(
            "STRIPE_WEBHOOK_SECRET missing or not a whsec_* secret"
        )
