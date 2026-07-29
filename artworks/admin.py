from django.conf import settings
from django.contrib import admin
from django.db.models import Max
from django.forms.models import BaseInlineFormSet

from artworks.models import Artist, ArtistTranslation
from project.admin_base import ModelAdminUnfoldBase
from unfold.admin import StackedInline


class ArtistTranslationFormSet(BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        existing_langs = set()
        if self.instance and self.instance.pk:
            existing_langs = set(self.queryset.values_list("language", flat=True))
        available_langs = [code for code, name in settings.LANGUAGES if code not in existing_langs]
        for i, form in enumerate(self.extra_forms):
            if i < len(available_langs):
                form.initial["language"] = available_langs[i]


class ArtistTranslationInline(StackedInline):
    model = ArtistTranslation
    formset = ArtistTranslationFormSet
    verbose_name = "Traducción"
    verbose_name_plural = "Traducciones (Español / Inglés)"
    max_num = len(settings.LANGUAGES)
    fields = ["language", "bio"]

    def get_extra(self, request, obj=None, **kwargs):
        if obj:
            existing_count = obj.translations.count()
            return max(0, len(settings.LANGUAGES) - existing_count)
        return len(settings.LANGUAGES)


@admin.register(Artist)
class ArtistAdmin(ModelAdminUnfoldBase):
    sidebar_icon = "palette"
    inlines = [ArtistTranslationInline]
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ["name", "email", "slug", "translations__bio"]
    list_filter = ["is_active"]
    fieldsets = (
        ("Personal Info", {
            "fields": (("name", "slug"), ("birth_year", "death_year"))
        }),
        ("Contact & Media", {
            "fields": ("email", "website", "photo")
        }),
        ("System Status", {
            "fields": (("is_active", "sort_order"),)
        }),
    )
    list_display = [
        "display_name",
        "display_email",
        "birth_year",
        "death_year",
        "display_active",
        "sort_order",
    ]

    def get_changeform_initial_data(self, request):
        initial = super().get_changeform_initial_data(request)
        max_order = Artist.objects.aggregate(Max("sort_order"))["sort_order__max"] or 0
        initial["sort_order"] = max_order + 1
        return initial

    @admin.display(description="Nombre", ordering="name")
    def display_name(self, obj):
        return obj.name

    @admin.display(description="Correo electrónico", ordering="email")
    def display_email(self, obj):
        return obj.email or "-"

    @admin.display(description="Activo", ordering="is_active", boolean=True)
    def display_active(self, obj):
        return obj.is_active
