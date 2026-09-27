"""Notifications for cash, artwork-sale, and online-subscription emails.

This is the only module allowed to send mail. Each notification sends
per-audience ``EmailMultiAlternatives`` messages (TXT + HTML, never CC):
a buyer and/or artist receipt and an admin notice (``EMAILS_NOTIFICATIONS``),
each with its own Spanish subject. Online-subscription mail uses the same
two-audience (artist + admin) shape as cash.

Email is best-effort: callers (admin actions, views, webhook
``transaction.on_commit`` callbacks, cron commands) must catch exceptions —
use ``send_best_effort`` — so a mail failure never rolls back an
already-persisted state change nor turns a webhook 200 into a 500.
"""

import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from core.mail_utils import send_audience, send_best_effort
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
    "reminder": (
        "Tu suscripción vence en 3 días",
        "[Enredarte] Suscripción por vencer — {artista}",
    ),
    "duetoday": (
        "Tu suscripción vence hoy",
        "[Enredarte] Suscripción vence hoy — {artista}",
    ),
    "overdue": (
        "Tu pago está vencido",
        "[Enredarte] Pago vencido — {artista}",
    ),
    "deactivated": (
        "Tu suscripción fue desactivada por falta de pago",
        "[Enredarte] Artista desactivado por no renovar — {artista}",
    ),
}


def _context(artist, actor):
    if actor is None:
        actor_name = "Operador"
    else:
        actor_name = getattr(actor, "username", None) or str(actor)
    ctx = {
        "artist": artist,
        "artist_name": artist.name,
        "plan": BillingPlan.get_solo(),
        "actor": actor,
        "actor_name": actor_name,
        "host": settings.HOST,
    }
    sub = getattr(artist, "subscription", None)
    renew = getattr(sub, "current_period_end", None)
    if renew is not None:
        from django.utils.formats import date_format

        ctx["renew_date"] = date_format(renew, "DATE_FORMAT")
    return ctx


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


def send_cash_reminder(artist, actor=None):
    """Remind artist + admins that a cash renew date is 3 days out."""
    _send_cash("reminder", artist, actor)


def send_cash_duetoday(artist, actor=None):
    """Remind artist + admins that a cash renew date is today."""
    _send_cash("duetoday", artist, actor)


def send_cash_overdue(artist, actor=None):
    """Notify artist + admins that a cash payment is overdue (past_due)."""
    _send_cash("overdue", artist, actor)


def send_cash_deactivated(artist, actor=None):
    """Notify artist + admins of deactivation for non-renewal."""
    _send_cash("deactivated", artist, actor)


# online subscription kind -> (artist subject, admin subject template).
_ONLINE_SUBJECTS = {
    "canceling": (
        "Tu suscripción en línea será cancelada",
        "[Enredarte] Suscripción en línea en cancelación — {artista}",
    ),
    "canceled": (
        "Tu suscripción en línea fue cancelada",
        "[Enredarte] Suscripción en línea cancelada — {artista}",
    ),
}


def _send_online(kind, subscription, actor=None):
    """Send artist + admin mails for an online subscription cancellation."""
    artist = subscription.artist
    artist_subject, admin_subject_tmpl = _ONLINE_SUBJECTS[kind]
    ctx = _context(artist, actor)
    send_audience(artist_subject, ctx, f"subscriptions/email/online_{kind}", [artist.email])
    if not settings.EMAILS_NOTIFICATIONS:
        logger.warning(
            "online email %s admin skipped: EMAILS_NOTIFICATIONS empty (artist=%s)",
            kind, artist.pk,
        )
        return
    send_audience(
        admin_subject_tmpl.format(artista=artist.name),
        ctx,
        f"subscriptions/email/online_{kind}_admin",
        settings.EMAILS_NOTIFICATIONS,
    )


def send_online_canceling(subscription, actor=None):
    """Notify artist + admin that an online subscription is canceling."""
    _send_online("canceling", subscription, actor)


def send_online_canceled(subscription, actor=None):
    """Notify artist + admin that an online subscription ended."""
    _send_online("canceled", subscription, actor)
