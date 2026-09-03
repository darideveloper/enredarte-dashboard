import logging
import os

from django.apps import AppConfig
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger(__name__)


class SubscriptionsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "subscriptions"
    verbose_name = "Suscripciones"

    def ready(self):
        env = os.getenv("ENV", "dev")
        if env != "dev":
            if not settings.STRIPE_SECRET_KEY or not settings.STRIPE_WEBHOOK_SECRET.startswith("whsec_"):
                raise ImproperlyConfigured("STRIPE_* missing: STRIPE_SECRET_KEY or STRIPE_WEBHOOK_SECRET (whsec_*) not configured")
            if not settings.STRIPE_API_VERSION:
                logger.warning("STRIPE_API_VERSION is empty; Stripe calls may use default version")