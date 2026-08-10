from django.contrib import admin
from django.shortcuts import redirect
from django.urls import reverse
from unfold.admin import ModelAdmin
from unfold.decorators import action


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

    @action(description="Editar", permissions=["change"])
    def edit(self, request, object_id):
        return redirect(
            reverse(
                f"admin:{self.model._meta.app_label}_{self.model._meta.model_name}_change",
                args=[object_id],
            )
        )
