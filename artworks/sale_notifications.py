"""Artwork-sale transactional emails (buyer / artist / admin audiences).

Owned by the `artworks` domain: every transition of `ArtworkOrder` fires a
per-audience Spanish mail. Best-effort and per-audience rendering come from
`core.mail_utils`; templates live under `artworks/templates/artworks/email/`.
"""

import logging

from django.conf import settings

from core.mail_utils import send_audience

logger = logging.getLogger(__name__)

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
        tmpl = f"artworks/email/sale_{kind}_{audience}"
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
        if send_audience(subject, ctx, tmpl, recipients):
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
