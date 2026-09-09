from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import redirect
from django.urls import reverse

from core.services.publishing import publish_changes


@staff_member_required(login_url="admin:login")
def publish_changes_view(request):
    try:
        publish_changes()
    except Exception as exc:
        messages.error(request, f"No se pudo publicar: {exc}")
    else:
        messages.success(
            request,
            "Cambios publicados correctamente, espere 5-10 minutos para verlos "
            "reflejados en la web (preferiblemente use una ventana de incógnito)",
        )
    return redirect(reverse("admin:index"))
