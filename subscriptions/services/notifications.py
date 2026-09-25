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


def _send_audience(subject, ctx, tmpl_name, recipients):
    """Send one TXT+HTML message to ``recipients``; return False if none."""
    if not recipients:
        return False
    text = render_to_string(f"subscriptions/email/{tmpl_name}.txt", ctx)
    html = render_to_string(f"subscriptions/email/{tmpl_name}.html", ctx)
    msg = EmailMultiAlternatives(subject, text, settings.EMAIL_FROM, recipients)
    msg.attach_alternative(html, "text/html")
    msg.send()
    return True


# artwork-sale kind -> audiences (subject templates per audience).
_SALE_AUDIENCES = {
    "reserved": ["buyer", "admin"],
    "paid": ["buyer", "artist", "admin"],
    "delivery_complete": ["buyer", "artist", "admin"],
    "shipped": ["buyer", "admin"],
    "delivered": ["buyer", "admin"],
    "cancelled": ["buyer", "artist", "admin"],
    "refunded": ["buyer", "artist", "admin"],
}

_SALE_SUBJECTS = {
    "reserved": {
        "buyer": "Tu compra está reservada / Your purchase is reserved",
        "admin": "[Enredarte] Nueva reserva — {artwork} ({order})",
    },
    "paid": {
        "buyer": "Tu pago fue confirmado / Payment confirmed",
        "artist": "Tu obra {title} se vendió",
        "admin": "[Enredarte] Venta pagada — {artwork} ({order})",
    },
    "delivery_complete": {
        "buyer": "Recibimos tus datos de entrega / Delivery details received",
        "artist": "Datos de entrega listos para {title}",
        "admin": "[Enredarte] Datos de entrega — {artwork} ({order})",
    },
    "shipped": {
        "buyer": "Tu obra va en camino / Your artwork is on its way",
        "admin": "[Enredarte] Pedido enviado — {artwork} ({order})",
    },
    "delivered": {
        "buyer": "Tu obra fue entregada / Your artwork was delivered",
        "admin": "[Enredarte] Pedido entregado — {artwork} ({order})",
    },
    "cancelled": {
        "buyer": "Tu pago no se completó / Payment not completed",
        "artist": "La reserva de {title} se liberó",
        "admin": "[Enredarte] Reserva cancelada — {artwork} ({order})",
    },
    "refunded": {
        "buyer": "Tu reembolso está en camino / Your refund is on the way",
        "artist": "Aviso de doble pago en {title}",
        "admin": "[Enredarte] Reembolso por doble venta — {artwork} ({order})",
    },
}


def _sale_context(order, checkout_url=None, refund_id=None):
    """Build the shared template context for an artwork-sale mail."""
    artwork = order.artwork
    artist = artwork.artist if getattr(artwork, "artist", None) else None
    title = (
        artwork.translated_title()
        if hasattr(artwork, "translated_title")
        else str(artwork)
    )
    return {
        "order": order,
        "order_slug": order.slug,
        "artwork": artwork,
        "artwork_title": title,
        "artist": artist,
        "artist_name": artist.name if artist else "",
        "buyer_email": order.buyer_email,
        "amount": order.amount,
        "currency": (order.currency or "").upper(),
        "host": settings.HOST,
        "admin_url": f"{settings.HOST}/admin/artworks/artworkorder/{order.pk}/change/",
        "checkout_url": (checkout_url or order.checkout_url or ""),
        "refund_id": refund_id or "",
    }


def _send_sale(kind, order, **extra):
    """Send per-audience mails for an artwork-sale transition.

    Fires one message per audience (never CC). Returns the number of
    audiences actually messaged, so callers know if anything was skipped.
    """
    ctx = _sale_context(
        order,
        checkout_url=extra.get("checkout_url"),
        refund_id=extra.get("refund_id"),
    )
    sent = 0
    for audience in _SALE_AUDIENCES[kind]:
        subject = _SALE_SUBJECTS[kind][audience].format(
            artwork=ctx["artwork_title"],
            order=order.slug,
            title=ctx["artwork_title"],
        )
        tmpl = f"sale_{kind}_{audience}"
        if audience == "buyer":
            recipients = [order.buyer_email]
        elif audience == "artist":
            artist = artwork_artist_email(order)
            if not artist:
                logger.warning(
                    "sale email %s artist skipped: artist without email (order=%s)",
                    kind, order.slug,
                )
                continue
            recipients = [artist]
        else:  # admin
            if not settings.EMAILS_NOTIFICATIONS:
                logger.warning(
                    "sale email %s admin skipped: EMAILS_NOTIFICATIONS empty (order=%s)",
                    kind, order.slug,
                )
                continue
            recipients = settings.EMAILS_NOTIFICATIONS
        if _send_audience(subject, ctx, tmpl, recipients):
            sent += 1
    return sent


def artwork_artist_email(order):
    """Return the artwork's artist email, or '' when none."""
    artwork = order.artwork
    artist = artwork.artist if getattr(artwork, "artist", None) else None
    return (artist.email if artist and artist.email else "")


def send_sale_reserved(order):
    """Notify buyer + admin that an artwork was reserved (checkout open)."""
    return _send_sale("reserved", order)


def send_sale_paid(order):
    """Notify buyer + admin + artist that a sale was paid (artwork sold)."""
    return _send_sale("paid", order)


def send_sale_delivery_complete(order):
    """Notify buyer + admin + artist that delivery data was submitted."""
    return _send_sale("delivery_complete", order)


def send_sale_shipped(order):
    """Notify buyer + admin that the order was shipped."""
    return _send_sale("shipped", order)


def send_sale_delivered(order):
    """Notify buyer + admin that the order was delivered."""
    return _send_sale("delivered", order)


def send_sale_cancelled(order):
    """Notify buyer + admin + artist that the reservation was released."""
    return _send_sale("cancelled", order)


def send_sale_refunded(order, refund_id=""):
    """Notify buyer + admin + artist of an automatic double-sale refund."""
    return _send_sale("refunded", order, refund_id=refund_id)


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
    _send_audience(artist_subject, ctx, f"online_{kind}", [artist.email])
    if not settings.EMAILS_NOTIFICATIONS:
        logger.warning(
            "online email %s admin skipped: EMAILS_NOTIFICATIONS empty (artist=%s)",
            kind, artist.pk,
        )
        return
    _send_audience(
        admin_subject_tmpl.format(artista=artist.name),
        ctx,
        f"online_{kind}_admin",
        settings.EMAILS_NOTIFICATIONS,
    )


def send_online_canceling(subscription, actor=None):
    """Notify artist + admin that an online subscription is canceling."""
    _send_online("canceling", subscription, actor)


def send_online_canceled(subscription, actor=None):
    """Notify artist + admin that an online subscription ended."""
    _send_online("canceled", subscription, actor)
