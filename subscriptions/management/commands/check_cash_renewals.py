"""Daily renewal check for cash subscriptions (external cron entrypoint).

For cash rows with a renew date (`current_period_end`), using one
project-timezone date: reminds at 3 days out and on the day, flips expired
rows to `past_due` (visible through the plan grace via `compute_is_active`),
and deactivates past-grace rows (`canceled`, hidden). Every branch notifies
the artist and the admin list. Null-renew rows are skipped.
"""

import logging
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from subscriptions.models import ArtistSubscription, BillingPlan
from subscriptions.services import notifications
from subscriptions.services.subscription_state import compute_is_active

logger = logging.getLogger(__name__)

REMINDER_DAYS = 3
ACTOR = "proceso automático"


class Command(BaseCommand):
    help = "Revisa renovaciones en efectivo: recuerda, vence y desactiva no renovados."

    def handle(self, *args, **options):
        today = timezone.localdate()
        grace = BillingPlan.get_solo().grace_period_days
        counts = {"reminder": 0, "duetoday": 0, "past_due": 0, "canceled": 0, "skipped": 0}
        rows = (
            ArtistSubscription.objects.filter(
                payment_method=ArtistSubscription.PaymentMethod.CASH,
                status__in=(
                    ArtistSubscription.Status.ACTIVE,
                    ArtistSubscription.Status.PAST_DUE,
                ),
                current_period_end__isnull=False,
            )
            .select_related("artist")
            .order_by("pk")
        )
        for sub in rows:
            try:
                self._process(sub, today, grace, counts)
            except Exception:
                logger.exception("check_cash_renewals failed artist=%s", sub.artist_id)
        msg = (
            "check_cash_renewals: "
            + ", ".join(f"{key}={counts[key]}" for key in ("reminder", "duetoday", "past_due", "canceled", "skipped"))
        )
        logger.info(msg)
        self.stdout.write(msg)

    def _process(self, sub, today, grace, counts):
        renew = timezone.localdate(sub.current_period_end)
        delta = (renew - today).days
        artist = sub.artist
        if sub.status == ArtistSubscription.Status.ACTIVE:
            if delta == REMINDER_DAYS:
                notifications.send_cash_reminder(artist, ACTOR)
                counts["reminder"] += 1
            elif delta == 0:
                notifications.send_cash_duetoday(artist, ACTOR)
                counts["duetoday"] += 1
            elif delta < 0:
                sub.status = ArtistSubscription.Status.PAST_DUE
                sub.last_synced_at = timezone.now()
                sub.save(update_fields=["status", "last_synced_at", "updated_at"])
                notifications.send_cash_overdue(artist, ACTOR)
                counts["past_due"] += 1
        elif sub.status == ArtistSubscription.Status.PAST_DUE:
            if today > renew + timedelta(days=grace):
                sub.status = ArtistSubscription.Status.CANCELED
                sub.last_synced_at = timezone.now()
                sub.save(update_fields=["status", "last_synced_at", "updated_at"])
                artist.is_active = compute_is_active(sub)
                artist.save(update_fields=["is_active", "updated_at"])
                notifications.send_cash_deactivated(artist, ACTOR)
                counts["canceled"] += 1
