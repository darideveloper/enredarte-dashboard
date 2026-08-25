"""Staff-gated admin endpoints for subscription control + landing pages.

Implementation choice (task 5.2): plain Django function-based views instead of
DRF. These endpoints are reached only from the Django admin change page and
only ever return redirects plus Django admin `messages` (plus the
`copy_to_clipboard` cookie on link flows) — a serializer/router abstraction
would add nothing.
"""

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext, gettext_lazy, override
from django.views.decorators.http import require_POST

from artworks.models import Artist
from subscriptions.models import ArtistSubscription, BillingPlan, epoch_to_datetime
from subscriptions.services import stripe_client
from subscriptions.services.subscription_state import compute_is_active

MSG_LINK_COPIED = gettext_lazy("Link copiado al portapapeles. Compártelo con el artista.")


def _artist_redirect_url(artist):
    return reverse("admin:artworks_artist_change", args=[artist.pk])


def _set_clipboard_cookie(response, url):
    response.set_cookie("copy_to_clipboard", url, max_age=10)


def _billing_blocked(artist):
    """Return an error message when link generation must be refused, else None."""
    if not artist.email:
        return gettext_lazy(
            "Este artista no tiene un correo electrónico. Captura uno antes de generar el link."
        )
    plan = BillingPlan.get_solo()
    if not plan.is_active_for_new_signups:
        return gettext_lazy("Las nuevas suscripciones están pausadas en el Plan de suscripción.")
    if not plan.stripe_price_id:
        return gettext_lazy(
            "Configura el `stripe_price_id` en Plan de suscripción antes de generar links."
        )
    return None


@require_POST
def generate_link(request, artist_id):
    artist = get_object_or_404(Artist, pk=artist_id)
    redirect_url = _artist_redirect_url(artist)

    blocked = _billing_blocked(artist)
    if blocked:
        messages.error(request, blocked)
        return redirect(redirect_url)

    plan = BillingPlan.get_solo()
    sub, _created = ArtistSubscription.objects.get_or_create(
        artist=artist,
        defaults={"status": ArtistSubscription.Status.PENDING},
    )

    if not sub.stripe_customer_id:
        customer = stripe_client.create_customer(artist.email)
        sub.stripe_customer_id = customer.id

    session = stripe_client.create_checkout_session(
        sub.stripe_customer_id, {"artist_id": str(artist.pk)}, plan.stripe_price_id
    )
    sub.signup_url = session.url
    sub.signup_url_expires_at = epoch_to_datetime(session.expires_at)
    sub.status = ArtistSubscription.Status.PENDING
    sub.last_synced_at = timezone.now()
    sub.save(
        update_fields=[
            "signup_url",
            "signup_url_expires_at",
            "status",
            "last_synced_at",
            "stripe_customer_id",
            "updated_at",
        ]
    )

    artist.is_active = compute_is_active(sub)
    artist.save(update_fields=["is_active", "updated_at"])

    messages.success(request, MSG_LINK_COPIED)
    response = redirect(redirect_url)
    _set_clipboard_cookie(response, sub.signup_url)
    return response


@require_POST
def regenerate_link(request, artist_id):
    artist = get_object_or_404(Artist, pk=artist_id)
    redirect_url = _artist_redirect_url(artist)

    blocked = _billing_blocked(artist)
    if blocked:
        messages.error(request, blocked)
        return redirect(redirect_url)

    sub = ArtistSubscription.objects.filter(artist=artist).first()
    if sub is None:
        return generate_link(request, artist_id)

    existing = stripe_client.expire_or_reuse_session(
        sub.signup_url, sub.signup_url_expires_at
    )
    if existing:
        messages.success(request, MSG_LINK_COPIED)
        response = redirect(redirect_url)
        _set_clipboard_cookie(response, existing)
        return response

    plan = BillingPlan.get_solo()
    if not sub.stripe_customer_id:
        customer = stripe_client.create_customer(artist.email)
        sub.stripe_customer_id = customer.id

    session = stripe_client.create_checkout_session(
        sub.stripe_customer_id, {"artist_id": str(artist.pk)}, plan.stripe_price_id
    )
    sub.signup_url = session.url
    sub.signup_url_expires_at = epoch_to_datetime(session.expires_at)
    sub.last_synced_at = timezone.now()
    sub.save(
        update_fields=[
            "signup_url",
            "signup_url_expires_at",
            "last_synced_at",
            "stripe_customer_id",
            "updated_at",
        ]
    )

    messages.success(request, MSG_LINK_COPIED)
    response = redirect(redirect_url)
    _set_clipboard_cookie(response, sub.signup_url)
    return response


@require_POST
def open_portal(request, artist_id):
    artist = get_object_or_404(Artist, pk=artist_id)
    redirect_url = _artist_redirect_url(artist)

    sub = ArtistSubscription.objects.filter(artist=artist).first()
    if sub is None or not sub.stripe_customer_id:
        messages.warning(request, gettext("Aún no se generó un link de pago para este artista."))
        return redirect(redirect_url)

    session = stripe_client.create_billing_portal_session(sub.stripe_customer_id)
    messages.success(request, gettext("Customer Portal: {url}").format(url=session.url))
    response = redirect(redirect_url)
    _set_clipboard_cookie(response, session.url)
    return response


@require_POST
def sync_from_stripe(request, artist_id):
    artist = get_object_or_404(Artist, pk=artist_id)
    redirect_url = _artist_redirect_url(artist)

    sub = ArtistSubscription.objects.filter(artist=artist).first()
    if sub is None or not sub.stripe_customer_id:
        messages.warning(request, gettext("Este artista aún no tiene un customer en Stripe."))
        return redirect(redirect_url)

    prev_label = sub.get_status_display()
    customer = stripe_client.fetch_customer(sub.stripe_customer_id)
    sub.customer_email = customer.email or sub.customer_email

    subs = stripe_client.list_subscriptions(sub.stripe_customer_id, limit=1)
    if not subs:
        sub.status = ArtistSubscription.Status.CANCELED
        sub.last_synced_at = timezone.now()
        sub.save(
            update_fields=["status", "customer_email", "last_synced_at", "updated_at"]
        )
    else:
        sub.apply_stripe_payload(subs[0])
        sub.save(update_fields=["customer_email", "updated_at"])

    artist.is_active = compute_is_active(sub)
    artist.save(update_fields=["is_active", "updated_at"])

    messages.success(
        request,
        gettext("Suscripción sincronizada: {prev} → {new}").format(
            prev=prev_label, new=sub.get_status_display()
        ),
    )
    return redirect(redirect_url)


def _preferred_language(request):
    """Lightweight Accept-Language sniff for the two landing pages."""
    accept = (request.META.get("HTTP_ACCEPT_LANGUAGE") or "es").split(",")[0].strip().lower()
    return "en" if accept.startswith("en") else "es"


def success(request):
    with override(_preferred_language(request)):
        return render(
            request,
            "subscriptions/success.html",
            {
                "heading": gettext("¡Gracias! Tu suscripción está activa."),
                "detail": gettext(
                    "La visibilidad en el sitio público se hará efectiva "
                    "una vez que el operador active tu cuenta."
                ),
            },
        )


def cancel(request):
    with override(_preferred_language(request)):
        return render(
            request,
            "subscriptions/cancel.html",
            {
                "heading": gettext("Tu pago fue cancelado."),
                "detail": gettext("Puedes intentarlo nuevamente cuando quieras."),
            },
        )


def portal_return(request):
    """Neutral landing shown after the artist leaves the Customer Portal.

    Kept deliberately generic: the artist may have updated their card, viewed
    invoices, or cancelled — the page must not claim the subscription is active.
    """
    with override(_preferred_language(request)):
        return render(
            request,
            "subscriptions/portal_return.html",
            {
                "heading": gettext("Gracias por usar el portal de gestión."),
                "detail": gettext("Tus cambios de suscripción fueron guardados."),
            },
        )