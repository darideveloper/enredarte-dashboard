"""Shared mail plumbing for domain mailers.

Both the subscription mailer (`subscriptions/services/notifications.py`) and
the artwork-sale mailer (`artworks/sale_notifications.py`) use these helpers so
the best-effort contract and the per-audience TXT+HTML rendering stay in one
place. The renderer takes a **full template base path** so each domain resolves
its own namespace (`subscriptions/email/*` vs `artworks/email/*`).
"""

import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


def send_best_effort(sender, *args, **kwargs):
    """Invoke a mail sender, swallowing + logging exceptions.

    Best-effort contract: callers (views, admin actions, webhook
    ``transaction.on_commit`` callbacks, cron commands) use this so a mail
    failure never propagates to the HTTP layer or rolls back state.
    """
    try:
        sender(*args, **kwargs)
    except Exception:
        logger.exception(
            "best-effort email send failed: %s", getattr(sender, "__name__", sender)
        )


def send_audience(subject, ctx, template_base, recipients):
    """Send one TXT+HTML message to ``recipients``; return False if none.

    ``template_base`` is a full path minus extension, e.g.
    ``"artworks/email/sale_paid_buyer"`` or ``"subscriptions/email/online_canceled"``.
    """
    if not recipients:
        return False
    text = render_to_string(f"{template_base}.txt", ctx)
    html = render_to_string(f"{template_base}.html", ctx)
    msg = EmailMultiAlternatives(subject, text, settings.EMAIL_FROM, recipients)
    msg.attach_alternative(html, "text/html")
    msg.send()
    return True
