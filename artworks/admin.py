from django.contrib import admin

from artworks.models import Artist, ArtistTranslation
from project.admin_base import ModelAdminUnfoldBase
from unfold.admin import StackedInline


class ArtistTranslationInline(StackedInline):
    model = ArtistTranslation
    verbose_name = "Traducción"
    verbose_name_plural = "Traducciones (Español / Inglés)"
    extra = 2
    fields = ["language", "bio"]


@admin.register(Artist)
class ArtistAdmin(ModelAdminUnfoldBase):
    sidebar_icon = "palette"
    inlines = [ArtistTranslationInline]
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ["name", "email", "slug", "translations__bio"]
    list_filter = ["is_active"]
    list_display = [
        "display_name",
        "display_email",
        "birth_year",
        "death_year",
        "display_active",
        "sort_order",
    ]

    @admin.display(description="Nombre", ordering="name")
    def display_name(self, obj):
        return obj.name

    @admin.display(description="Correo electrónico", ordering="email")
    def display_email(self, obj):
        return obj.email or "-"

    @admin.display(description="Activo", ordering="is_active", boolean=True)
    def display_active(self, obj):
        return obj.is_active
