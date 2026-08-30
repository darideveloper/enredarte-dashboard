"""Landing pages for Stripe subscription flows + webhook (in project/urls.py)."""

from django.shortcuts import render
from django.utils.translation import gettext, override


def _preferred_language(request):
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
                    "La visibilidad de tu artista en el sitio público es automática "
                    "al confirmarse el pago."
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
    with override(_preferred_language(request)):
        return render(
            request,
            "subscriptions/portal_return.html",
            {
                "heading": gettext("Gracias por usar el portal de gestión."),
                "detail": gettext("Tus cambios de suscripción fueron guardados."),
            },
        )
