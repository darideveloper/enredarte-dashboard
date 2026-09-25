"""Shared Stripe time helpers."""

from datetime import datetime, timezone as dt_timezone


def epoch_to_datetime(ts):
    """Convert a Stripe unix timestamp to an aware datetime (UTC), or None."""
    if not ts:
        return None
    return datetime.fromtimestamp(ts, tz=dt_timezone.utc)
