"""Notifications for manual cash subscriptions.

This is the only module allowed to send mail. Each cash transition sends
two separate messages (never CC): an artist receipt and an admin notice
with its own subject. All copy is Spanish, matching the admin language.

Email is best-effort: callers (admin actions) must catch exceptions so a
mail failure never rolls back an already-persisted state change.
"""

import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from subscriptions.models import BillingPlan

logger = logging.getLogger(__name__)

# transition -> (artist subject, admin subject template)
_SUBJECTS = {
    "pending": (
        "Tu registro de pago en efectivo está pendiente",
        "[Enredarte] Artista marcado como efectivo — {artista}",
    ),
    "active": (
        "Tu pago en efectivo fue confirmado",
        "[Enredarte] Pago en efectivo confirmado — {artista}",
    ),
    "canceled": (
        "Tu suscripción en efectivo fue cancelada",
        "[Enredarte] Suscripción en efectivo cancelada — {artista}",
    ),
}


def _context(artist, actor):
    if actor is None:
        actor_name = "Operador"
    else:
        actor_name = getattr(actor, "username", None) or str(actor)
    return {
        "artist": artist,
        "artist_name": artist.name,
        "plan": BillingPlan.get_solo(),
        "actor": actor,
        "actor_name": actor_name,
        "host": settings.HOST,
    }


def _send_cash(kind, artist, actor):
    """Send the artist receipt + admin notice for a cash transition."""
    artist_subject, admin_template = _SUBJECTS[kind]
    ctx = _context(artist, actor)
    text = render_to_string(f"subscriptions/email/cash_{kind}.txt", ctx)
    html = render_to_string(f"subscriptions/email/cash_{kind}.html", ctx)

    artist_msg = EmailMultiAlternatives(
        artist_subject, text, settings.EMAIL_FROM, [artist.email],
    )
    artist_msg.attach_alternative(html, "text/html")
    artist_msg.send()

    recipients = settings.EMAILS_NOTIFICATIONS
    if not recipients:
        logger.warning(
            "cash email %s admin skipped: EMAILS_NOTIFICATIONS empty (artist=%s)",
            kind, artist.pk,
        )
        return
    admin_text = render_to_string(f"subscriptions/email/cash_{kind}_admin.txt", ctx)
    admin_html = render_to_string(f"subscriptions/email/cash_{kind}_admin.html", ctx)
    admin_msg = EmailMultiAlternatives(
        admin_template.format(artista=artist.name),
        admin_text, settings.EMAIL_FROM, recipients,
    )
    admin_msg.attach_alternative(admin_html, "text/html")
    admin_msg.send()


def send_cash_pending(artist, actor=None):
    """Notify artist + admins that a cash subscription was registered."""
    _send_cash("pending", artist, actor)


def send_cash_active(artist, actor=None):
    """Notify artist + admins that a cash payment was confirmed."""
    _send_cash("active", artist, actor)


def send_cash_canceled(artist, actor=None):
    """Notify artist + admins that a cash subscription was canceled."""
    _send_cash("canceled", artist, actor)
