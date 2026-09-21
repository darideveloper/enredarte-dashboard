"""Release stale artwork reservations (external cron entrypoint)."""

import logging

from django.core.management.base import BaseCommand
from django.utils import timezone

from artworks.models import ArtworkOrder, ArtworkOrderStatus
from artworks.services import cancel_order

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Cancela pedidos pendientes con sesión expirada y libera la obra."

    def handle(self, *args, **options):
        now = timezone.now()
        expired = ArtworkOrder.objects.select_related("artwork").filter(
            status=ArtworkOrderStatus.PENDING_PAYMENT,
            session_expires_at__lt=now,
        )
        released = 0
        for order in expired:
            if cancel_order(order):
                from subscriptions.services import notifications

                notifications.send_best_effort(notifications.send_sale_cancelled, order)
                released += 1
        msg = f"release_expired_orders: {released} liberada(s)"
        logger.info(msg)
        self.stdout.write(msg)
