from datetime import datetime
from io import BytesIO
from urllib.parse import quote

from django.contrib import admin, messages
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from unfold.admin import ModelAdmin
from unfold.decorators import action


def _excel_response(workbook, filename):
    """Serialize an openpyxl Workbook into an HttpResponse with RFC 5987 disposition."""
    buf = BytesIO()
    workbook.save(buf)
    buf.seek(0)
    quoted = quote(filename)
    response = HttpResponse(
        buf.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = (
        f'attachment; filename="{filename}"; filename*=utf-8\'\'{quoted}'
    )
    return response


class TranslatableNameAdminMixin:
    """Admin mixin for models whose display name lives in translation rows.

    Prefetches `translations` on the changelist queryset and renders the
    ES-first name from that cache in Python (no per-row queries). Intended for
    the `TranslatableName` catalog models.
    """

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("translations")

    @admin.display(description="Nombre")
    def display_name(self, obj):
        translations = list(obj.translations.all())
        es = next((t for t in translations if t.language == "es"), None)
        if es:
            return es.name
        return translations[0].name if translations else "-"


class ModelAdminUnfoldBase(ModelAdmin):
    sidebar_icon = "database"
    compressed_fields = True
    warn_unsaved_form = True
    list_filter_sheet = False
    change_form_show_cancel_button = True
    actions_row = ["edit"]
    actions = ["export_selected", "export_selected_with_related"]

    @action(description="Editar", permissions=["change"])
    def edit(self, request, object_id):
        return redirect(
            reverse(
                f"admin:{self.model._meta.app_label}_{self.model._meta.model_name}_change",
                args=[object_id],
            )
        )

    @action(description="Exportar a Excel", icon="download", permissions=["view"])
    def export_selected(self, request, queryset):
        if not queryset.exists():
            self.message_user(
                request, "Selecciona al menos una fila para exportar.", messages.WARNING
            )
            return None
        from utils.excel_export import build_workbook_for_queryset

        wb = build_workbook_for_queryset(self.model, queryset, include_related=False)
        ts = datetime.now().strftime("%Y%m%d_%H%M")
        filename = f"{self.model._meta.model_name}_{ts}.xlsx"
        return _excel_response(wb, filename)

    def has_export_selected_permission(self, request, obj=None):
        return self.has_view_permission(request, obj)

    @action(description="Exportar a Excel (con relacionados)", icon="download", permissions=["view"])
    def export_selected_with_related(self, request, queryset):
        if not queryset.exists():
            self.message_user(
                request, "Selecciona al menos una fila para exportar.", messages.WARNING
            )
            return None
        from utils.excel_export import build_workbook_for_queryset

        wb = build_workbook_for_queryset(self.model, queryset, include_related=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M")
        filename = f"{self.model._meta.model_name}_{ts}.xlsx"
        return _excel_response(wb, filename)

    def has_export_selected_with_related_permission(self, request, obj=None):
        return self.has_view_permission(request, obj)
