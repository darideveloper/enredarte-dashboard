from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from artworks.admin import TranslationInline
from blog.models import BlogImage, Post, PostTranslation
from project.admin_base import ModelAdminUnfoldBase
from utils.media import get_media_url


class PostTranslationInline(TranslationInline):
    model = PostTranslation
    fields = ["language", "title", "description", "keywords", "content"]


@admin.register(Post)
class PostAdmin(ModelAdminUnfoldBase):
    sidebar_icon = "article"
    inlines = [PostTranslationInline]
    date_hierarchy = "published_at"
    list_per_page = 25
    search_fields = [
        "slug",
        "translations__title",
        "translations__description",
        "translations__keywords",
        "author",
    ]
    list_filter = ["is_active", "created_at", "published_at", "author"]
    readonly_fields = ["display_banner_preview"]
    fieldsets = (
        (
            "Información principal",
            {
                "fields": (
                    "author",
                    "published_at",
                    "banner_image",
                    "display_banner_preview",
                )
            },
        ),
        (
            "Configuración del sistema",
            {
                "fields": (
                    "slug",
                    "is_active",
                )
            },
        ),
    )
    list_display = [
        "display_banner",
        "display_title",
        "author",
        "published_at",
        "display_active",
    ]

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("translations")

    def get_changeform_initial_data(self, request):
        initial = super().get_changeform_initial_data(request)
        initial["published_at"] = timezone.now()
        return initial

    @admin.display(description="Banner")
    def display_banner(self, obj):
        if obj.banner_image:
            return format_html('<img src="{}" class="img-preview img-preview--sm" />', obj.banner_image.url)
        return "-"

    @admin.display(description="Vista previa del banner")
    def display_banner_preview(self, obj):
        if obj.banner_image:
            return format_html('<img src="{}" class="img-preview--banner" />', obj.banner_image.url)
        return "Sin banner asignado"

    @admin.display(description="Título")
    def display_title(self, obj):
        translations = list(obj.translations.all())
        es = next((t for t in translations if t.language == "es"), None)
        if es:
            return es.title
        return translations[0].title if translations else (obj.slug or "-")

    @admin.display(description="Activo", ordering="is_active", boolean=True)
    def display_active(self, obj):
        return obj.is_active

    class Media:
        js = ["js/blog_slug_autofill.js"]


@admin.register(BlogImage)
class BlogImageAdmin(ModelAdminUnfoldBase):
    sidebar_icon = "image"
    list_per_page = 25
    date_hierarchy = "created_at"
    actions_row = ["edit"]
    search_fields = ["name"]
    list_filter = ["created_at"]
    list_display = ["display_preview", "name", "display_url", "created_at"]
    readonly_fields = ["display_preview_large", "display_url"]
    fieldsets = (
        (
            "Información de la imagen",
            {"fields": ("name", "image", "display_preview_large", "display_url")},
        ),
    )

    @admin.display(description="Vista previa")
    def display_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" class="img-preview img-preview--sm" />', obj.image.url)
        return "-"

    @admin.display(description="Vista previa")
    def display_preview_large(self, obj):
        if obj.image:
            return format_html('<img src="{}" class="img-preview--form" />', obj.image.url)
        return "-"

    @admin.display(description="URL")
    def display_url(self, obj):
        if obj.image:
            return obj.image.url
        return "-"

    def change_view(self, request, object_id, form_url="", extra_context=None):
        extra_context = extra_context or {}
        obj = self.get_object(request, object_id)
        url = get_media_url(obj.image.url) if obj and obj.image else None
        extra_context["copy_button_extra_attrs"] = (
            mark_safe(f'type="button" data-copy-url="{url}"') if url else None
        )
        return super().change_view(request, object_id, form_url, extra_context)

    class Media:
        js = ["js/copy_clipboard.js"]
