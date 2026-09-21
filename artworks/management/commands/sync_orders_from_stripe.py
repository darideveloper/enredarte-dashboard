"""Reconcile pending artwork orders against Stripe (drift recovery)."""

import logging

from django.core.management.base import BaseCommand

from artworks.models import ArtworkOrder, ArtworkOrderStatus
from artworks.services import apply_paid_transition, cancel_order

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Sincroniza pedidos pendientes con Stripe (solo lectura + transiciones)."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="No modifica nada, solo reporta.")

    def handle(self, *args, **options):
        from subscriptions.services import stripe_client

        dry_run = options["dry_run"]
        pending = ArtworkOrder.objects.select_related("artwork").filter(
            status=ArtworkOrderStatus.PENDING_PAYMENT
        )
        paid = cancelled = checked = 0
        for order in pending:
            checked += 1
            try:
                session = stripe_client.retrieve_checkout_session(order.stripe_checkout_session_id)
            except Exception:
                logger.exception("sync order=%s retrieve failed", order.slug)
                continue
            data = session if isinstance(session, dict) else {}
            def _get(key):
                return data.get(key) if isinstance(data, dict) else getattr(session, key, None)
            payment_status = _get("payment_status")
            status_value = _get("status")
            if dry_run:
                logger.info("sync dry-run order=%s paid=%s status=%s", order.slug, payment_status, status_value)
                continue
            if payment_status == "paid":
                pi = _get("payment_intent") or ""
                details = _get("customer_details") or {}
                name = details.get("name", "") if isinstance(details, dict) else ""
                if apply_paid_transition(order, str(pi or ""), order.buyer_email, name or ""):
                    from subscriptions.services import notifications

                    notifications.send_best_effort(notifications.send_sale_paid, order)
                    paid += 1
            elif status_value == "expired":
                if cancel_order(order):
                    from subscriptions.services import notifications

                    notifications.send_best_effort(notifications.send_sale_cancelled, order)
                    cancelled += 1
        msg = f"sync_orders_from_stripe: {checked} revisada(s), {paid} pagada(s), {cancelled} cancelada(s)"
        logger.info(msg)
        self.stdout.write(msg)
