"""Shared admin rendering helpers for subscriptions."""

from django.utils.html import format_html

from subscriptions.models import ArtistSubscription

_BADGE_STYLES = {
    ArtistSubscription.Status.PENDING: ("#fef3c7", "#92400e"),
    ArtistSubscription.Status.ACTIVE: ("#dcfce7", "#166534"),
    ArtistSubscription.Status.PAST_DUE: ("#fee2e2", "#991b1b"),
    ArtistSubscription.Status.CANCELING: ("#fef3c7", "#92400e"),
    ArtistSubscription.Status.CANCELED: ("#fee2e2", "#991b1b"),
}


def _muted_badge():
    return format_html(
        '<span style="color:#6b7280;font-size:12px">Sin suscripción</span>'
    )


def _badge(status, label):
    bg, fg = _BADGE_STYLES.get(status, ("#f3f4f6", "#374151"))
    return format_html(
        '<span style="background:{};color:{};padding:2px 10px;'
        'border-radius:9999px;font-size:12px;font-weight:500">{}</span>',
        bg,
        fg,
        label,
    )


def subscription_badge(subscription):
    """Render an `ArtistSubscription.status` as a colored pill badge.

    Returns the muted literal "Sin suscripción" when `subscription` is None.
    Inline styles are used so the badge renders regardless of the compiled
    CSS shipped with django-unfold.
    """
    if subscription is None:
        return _muted_badge()
    return _badge(subscription.status, subscription.get_status_display())


def subscription_badge_from_artist(artist_row):
    """Render the badge from Artist changelist annotations (no per-row queries)."""
    if not getattr(artist_row, "_has_subscription", False):
        return _muted_badge()
    status = artist_row._subscription_status
    label = ArtistSubscription(status=status).get_status_display()
    return _badge(status, label)