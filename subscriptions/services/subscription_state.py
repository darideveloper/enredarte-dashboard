"""Pure derivation of Artist.is_active from subscription state.

`compute_is_active` is the single source of truth for the boolean that gates
an artist's visibility on the public site. Webhook handlers and admin actions
call this helper (never derive the boolean inline) so manual and webhook-driven
changes cannot disagree.
"""

from datetime import timedelta

from django.utils import timezone

from subscriptions.models import ArtistSubscription, BillingPlan


def compute_is_active(subscription, artist=None):
    """Return the canonical boolean for `Artist.is_active`.

    `subscription` is an `ArtistSubscription` or `None`. With `None`, the
    artist's own current `is_active` is returned unchanged (preserving any
    manual operator toggle); pass the artist in that case.

    Rules:
    - active → visible (True).
    - pending → NOT visible (an unpaid, link-generated artist must not appear
      on the public site until the first successful payment).
    - canceling → visible until `current_period_end`.
    - past_due → visible while `current_period_end + grace_period_days` is in
      the future.
    - canceled → never visible.
    """
    if subscription is None:
        if artist is None:
            raise ValueError("artist is required when subscription is None")
        return artist.is_active

    status = subscription.status
    if status == ArtistSubscription.Status.ACTIVE:
        return True

    now = timezone.now()

    if status == ArtistSubscription.Status.CANCELING:
        if subscription.current_period_end is None:
            return True
        return subscription.current_period_end > now

    if status == ArtistSubscription.Status.PAST_DUE:
        if subscription.current_period_end is None:
            return True
        grace = timedelta(days=BillingPlan.get_solo().grace_period_days)
        return now < subscription.current_period_end + grace

    return False  # PENDING or CANCELED