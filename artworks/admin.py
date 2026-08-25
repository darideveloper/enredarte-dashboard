from django import forms
from django.conf import settings
from django.contrib import admin
from django.contrib.admin import RelatedOnlyFieldListFilter
from django.core.exceptions import ValidationError
from django.db.models import Count, Exists, OuterRef, Q, Subquery
from django.forms.models import BaseInlineFormSet
from django.utils import timezone
from django.utils.html import format_html, format_html_join

from artworks.admin_filters import YearFilter, has_related_filter
from artworks.models import (
    ArtCurator,
    ArtCuratorTranslation,
    Artist,
    ArtistSocialLink,
    ArtistTranslation,
    Artwork,
    ArtworkGallery,
    ArtworkImage,
    ArtworkStatus,
    ArtworkTranslation,
    Discipline,
    DisciplineTranslation,
    Format,
    FormatTranslation,
    Gallery,
    GalleryTranslation,
    Location,
    LocationTranslation,
    Scale,
    ScaleTranslation,
    Technique,
    TechniqueTranslation,
    Theme,
    ThemeTranslation,
)
from project.admin_base import ModelAdminUnfoldBase, TranslatableNameAdminMixin
from subscriptions.admin_helpers import subscription_badge_from_artist
from subscriptions.models import ArtistSubscription
from unfold.admin import StackedInline, TabularInline


class TranslationInlineFormSet(BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        existing_langs = set()
        if self.instance and self.instance.pk:
            existing_langs = set(self.queryset.values_list("language", flat=True))
        available_langs = [code for code, name in settings.LANGUAGES if code not in existing_langs]
        for i, form in enumerate(self.extra_forms):
            if i < len(available_langs):
                form.initial["language"] = available_langs[i]

    def clean(self):
        super().clean()
        excluded = {"language", "DELETE", "id"}
        if self.fk:
            excluded.add(self.fk.name)
        filled = 0
        for form in self.forms:
            data = form.cleaned_data or {}
            if data.get("DELETE"):
                continue
            if any(value for key, value in data.items() if key not in excluded):
                filled += 1
        if filled != len(settings.LANGUAGES):
            labels = ", ".join(name for code, name in settings.LANGUAGES)
            raise ValidationError(
                f"Se requieren exactamente {len(settings.LANGUAGES)} traducciones ({labels})."
            )


class TranslationInline(StackedInline):
    formset = TranslationInlineFormSet
    verbose_name = "Traducción"
    verbose_name_plural = "Traducciones (Español / Inglés)"
    can_delete = False
    min_num = len(settings.LANGUAGES)
    max_num = len(settings.LANGUAGES)
    validate_min = True
    validate_max = True

    def get_extra(self, request, obj=None, **kwargs):
        if obj:
            existing_count = obj.translations.count()
            return max(0, len(settings.LANGUAGES) - existing_count)
        return len(settings.LANGUAGES)


class ArtistTranslationInline(TranslationInline):
    model = ArtistTranslation
    fields = ["language", "bio"]


class ArtistSocialLinkInline(TabularInline):
    model = ArtistSocialLink
    fields = ["platform", "url"]
    verbose_name = "Red social"
    verbose_name_plural = "Redes sociales"
    extra = 1


class ArtCuratorTranslationInline(TranslationInline):
    model = ArtCuratorTranslation
    fields = ["language", "bio"]


class DisciplineTranslationInline(TranslationInline):
    model = DisciplineTranslation
    fields = ["language", "name"]


class TechniqueTranslationInline(TranslationInline):
    model = TechniqueTranslation
    fields = ["language", "name"]


class ThemeTranslationInline(TranslationInline):
    model = ThemeTranslation
    fields = ["language", "name"]


class FormatTranslationInline(TranslationInline):
    model = FormatTranslation
    fields = ["language", "name"]


class ScaleTranslationInline(TranslationInline):
    model = ScaleTranslation
    fields = ["language", "name"]


class GalleryTranslationInline(TranslationInline):
    model = GalleryTranslation
    fields = ["language", "name", "description"]


class LocationTranslationInline(TranslationInline):
    model = LocationTranslation
    fields = ["language", "name"]


class ArtworkGalleryInline(TabularInline):
    model = ArtworkGallery
    fields = ["artwork"]
    verbose_name = "Obra de arte"
    verbose_name_plural = "Obras de arte exhibidas"
    ordering_field = "sort_order"
    hide_ordering_field = True
    extra = 1


class GalleryArtworkInline(TabularInline):
    model = ArtworkGallery
    fields = ["gallery"]
    verbose_name = "Galería"
    verbose_name_plural = "Galerías donde se exhibe esta obra"
    ordering_field = "sort_order"
    hide_ordering_field = True
    extra = 1


class ArtistAvailableWorksFilter(admin.SimpleListFilter):
    title = "Obras disponibles"
    parameter_name = "has_available"

    def lookups(self, request, model_admin):
        return (
            ("with", "Con obras disponibles"),
            ("without", "Sin obras disponibles"),
        )

    def queryset(self, request, queryset):
        def has_available():
            return queryset.model.objects.filter(
                pk=OuterRef("pk"),
                artworks__is_active=True,
                artworks__status=ArtworkStatus.AVAILABLE,
            )

        if self.value() == "with":
            return queryset.filter(Exists(has_available()))
        if self.value() == "without":
            return queryset.filter(~Exists(has_available()))
        return queryset


@admin.register(Artist)
class ArtistAdmin(ModelAdminUnfoldBase):
    sidebar_icon = "palette"
    inlines = [ArtistTranslationInline, ArtistSocialLinkInline]
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ["name", "email", "slug", "translations__bio"]
    list_filter = [
        "is_active",
        "created_at",
        ("location", RelatedOnlyFieldListFilter),
        has_related_filter("artworks", "obras", "has_artworks"),
        ArtistAvailableWorksFilter,
    ]
    list_per_page = 50
    fieldsets = (
        ("Datos personales", {
            "fields": (("name", "slug"), ("birth_year", "death_year"), "location")
        }),
        ("Contacto y medios", {
            "fields": ("email", "website", "photo")
        }),
        ("Resumen", {
            "fields": (
                "display_techniques_detail",
                "display_available_detail",
                "display_new_additions_detail",
                "display_highlighted_detail",
                "display_most_viewed_detail",
                "display_curations_detail",
            )
        }),
        ("Estado del sistema", {
            "fields": (("is_active",),)
        }),
    )
    readonly_fields = [
        "display_techniques_detail",
        "display_available_detail",
        "display_new_additions_detail",
        "display_highlighted_detail",
        "display_most_viewed_detail",
        "display_curations_detail",
    ]
    list_display = [
        "display_name",
        "display_email",
        "birth_year",
        "death_year",
        "display_artworks_count",
        "display_available_count",
        "display_techniques_count",
        "display_highlighted_count",
        "display_galleries_count",
        "subscription_status_badge",
        "display_active",
    ]

    def get_queryset(self, request):
        subscription_exists = Exists(
            ArtistSubscription.objects.filter(artist=OuterRef("pk"))
        )
        subscription_status = Subquery(
            ArtistSubscription.objects.filter(artist=OuterRef("pk")).values("status")[:1]
        )
        return (
            super().get_queryset(request)
            .annotate(
                _has_subscription=subscription_exists,
                _subscription_status=subscription_status,
            )
            .annotate(
                _artworks_count=Count("artworks", filter=Q(artworks__is_active=True), distinct=True),
                _available_count=Count(
                    "artworks",
                    filter=Q(artworks__is_active=True, artworks__status=ArtworkStatus.AVAILABLE),
                    distinct=True,
                ),
                _techniques_count=Count("artworks__techniques", distinct=True),
                _highlighted_count=Count(
                    "artworks",
                    filter=Q(artworks__is_active=True, artworks__is_highlighted=True),
                    distinct=True,
                ),
                _galleries_count=Count(
                    "artworks__gallery_links__gallery",
                    filter=Q(artworks__gallery_links__gallery__is_active=True),
                    distinct=True,
                ),
            )
        )

    @admin.display(description="Nombre", ordering="name")
    def display_name(self, obj):
        return obj.name

    @admin.display(description="Correo electrónico", ordering="email")
    def display_email(self, obj):
        return obj.email or "-"

    @admin.display(description="Activo", ordering="is_active", boolean=True)
    def display_active(self, obj):
        return obj.is_active

    @admin.display(description="Suscripción")
    def subscription_status_badge(self, obj):
        return subscription_badge_from_artist(obj)

    def change_view(self, request, object_id, form_url="", extra_context=None):
        extra_context = extra_context or {}
        artist = self.get_object(request, object_id)
        sub = getattr(artist, "subscription", None) if artist else None
        extra_context["subscription_controls"] = {
            "no_subscription": sub is None,
            "has_customer": bool(sub and sub.stripe_customer_id),
        }
        return super().change_view(request, object_id, form_url, extra_context)

    class Media:
        js = ["js/copy_clipboard.js"]

    @staticmethod
    def _translated_name(holder):
        es = holder.translations.filter(language="es").first()
        if es:
            return es.name
        first = holder.translations.first()
        return first.name if first else "-"

    @staticmethod
    def _artwork_title(artwork):
        es = artwork.translations.filter(language="es").first()
        if es:
            return es.title
        first = artwork.translations.first()
        return first.title if first else artwork.slug

    @admin.display(description="Obras")
    def display_artworks_count(self, obj):
        return obj._artworks_count

    @admin.display(description="Disponibles")
    def display_available_count(self, obj):
        return obj._available_count

    @admin.display(description="Técnicas")
    def display_techniques_count(self, obj):
        return obj._techniques_count

    @admin.display(description="Destacadas")
    def display_highlighted_count(self, obj):
        return obj._highlighted_count

    @admin.display(description="Galerías")
    def display_galleries_count(self, obj):
        return obj._galleries_count

    @admin.display(description="Técnicas")
    def display_techniques_detail(self, obj):
        names = [self._translated_name(t) for t in obj.techniques]
        return ", ".join(names) if names else "-"

    @admin.display(description="Obras disponibles")
    def display_available_detail(self, obj):
        return f"{obj.available_artworks.count()} obra(s) disponible(s)"

    @admin.display(description="Nuevas incorporaciones")
    def display_new_additions_detail(self, obj):
        rows = [(self._artwork_title(a), a.year) for a in obj.new_additions]
        if not rows:
            return "-"
        return format_html_join("", "<div>- {0} ({1})</div>", rows)

    @admin.display(description="Destacadas")
    def display_highlighted_detail(self, obj):
        titles = [self._artwork_title(a) for a in obj.highlighted_artworks]
        if not titles:
            return "-"
        return format_html_join("", "<div>- {0}</div>", [(t,) for t in titles])

    @admin.display(description="Más visitadas")
    def display_most_viewed_detail(self, obj):
        rows = [(self._artwork_title(a), a.views_count) for a in obj.most_viewed]
        if not rows:
            return "-"
        return format_html_join("", "<div>- {0} — {1} visitas</div>", rows)

    @admin.display(description="Curadurías (galerías)")
    def display_curations_detail(self, obj):
        names = [self._translated_name(g) for g in obj.curations]
        return ", ".join(names) if names else "-"


@admin.register(ArtCurator)
class ArtCuratorAdmin(ModelAdminUnfoldBase):
    sidebar_icon = "person_check"
    inlines = [ArtCuratorTranslationInline]
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ["name", "email", "slug", "translations__bio"]
    list_filter = [
        "is_active",
        has_related_filter("curated_galleries", "galerías", "has_galleries"),
    ]
    fieldsets = (
        ("Datos personales", {
            "fields": (("name", "slug"),)
        }),
        ("Contacto y medios", {
            "fields": ("email", "website", "photo")
        }),
        ("Estado del sistema", {
            "fields": (("is_active",),)
        }),
    )
    list_display = [
        "display_name",
        "display_email",
        "display_active",
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


@admin.register(Discipline)
class DisciplineAdmin(TranslatableNameAdminMixin, ModelAdminUnfoldBase):
    sidebar_icon = "label"
    inlines = [DisciplineTranslationInline]
    search_fields = ["slug", "translations__name"]
    list_filter = [
        "is_active",
        has_related_filter("artworks", "obras", "has_artworks"),
    ]
    fieldsets = (
        ("Información del sistema", {
            "fields": ("slug", "is_active")
        }),
    )
    list_display = ["display_name", "slug", "display_active"]

    @admin.display(description="Activo", ordering="is_active", boolean=True)
    def display_active(self, obj):
        return obj.is_active


@admin.register(Technique)
class TechniqueAdmin(TranslatableNameAdminMixin, ModelAdminUnfoldBase):
    sidebar_icon = "brush"
    inlines = [TechniqueTranslationInline]
    search_fields = ["slug", "translations__name"]
    list_filter = [
        "is_active",
        has_related_filter("artworks", "obras", "has_artworks"),
    ]
    fieldsets = (
        ("Información del sistema", {
            "fields": ("slug", "is_active")
        }),
    )
    list_display = ["display_name", "slug", "display_active"]

    @admin.display(description="Activo", ordering="is_active", boolean=True)
    def display_active(self, obj):
        return obj.is_active


@admin.register(Theme)
class ThemeAdmin(TranslatableNameAdminMixin, ModelAdminUnfoldBase):
    sidebar_icon = "topic"
    inlines = [ThemeTranslationInline]
    search_fields = ["slug", "translations__name"]
    list_filter = [
        "is_active",
        has_related_filter("artworks", "obras", "has_artworks"),
    ]
    fieldsets = (
        ("Información del sistema", {
            "fields": ("slug", "is_active")
        }),
    )
    list_display = ["display_name", "slug", "display_active"]

    @admin.display(description="Activo", ordering="is_active", boolean=True)
    def display_active(self, obj):
        return obj.is_active


@admin.register(Format)
class FormatAdmin(TranslatableNameAdminMixin, ModelAdminUnfoldBase):
    sidebar_icon = "view_module"
    inlines = [FormatTranslationInline]
    search_fields = ["slug", "translations__name"]
    list_filter = [
        "is_active",
        has_related_filter("artworks", "obras", "has_artworks"),
    ]
    fieldsets = (
        ("Información del sistema", {
            "fields": ("slug", "is_active")
        }),
    )
    list_display = ["display_name", "slug", "display_active"]

    @admin.display(description="Activo", ordering="is_active", boolean=True)
    def display_active(self, obj):
        return obj.is_active


@admin.register(Scale)
class ScaleAdmin(TranslatableNameAdminMixin, ModelAdminUnfoldBase):
    sidebar_icon = "straighten"
    inlines = [ScaleTranslationInline]
    search_fields = ["slug", "translations__name"]
    list_filter = [
        "is_active",
        has_related_filter("artworks", "obras", "has_artworks"),
    ]
    fieldsets = (
        ("Información del sistema", {
            "fields": ("slug", "is_active")
        }),
    )
    list_display = ["display_name", "slug", "display_active"]

    @admin.display(description="Activo", ordering="is_active", boolean=True)
    def display_active(self, obj):
        return obj.is_active


@admin.register(Location)
class LocationAdmin(TranslatableNameAdminMixin, ModelAdminUnfoldBase):
    sidebar_icon = "location_on"
    inlines = [LocationTranslationInline]
    search_fields = ["slug", "translations__name"]
    list_filter = [
        "is_active",
        has_related_filter("artworks", "obras", "has_artworks"),
    ]
    fieldsets = (
        ("Información del sistema", {
            "fields": ("slug", "is_active")
        }),
    )
    list_display = ["display_name", "slug", "display_active"]

    @admin.display(description="Activo", ordering="is_active", boolean=True)
    def display_active(self, obj):
        return obj.is_active


class GalleryAdminForm(forms.ModelForm):
    class Meta:
        model = Gallery
        fields = "__all__"

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("is_primary", False):
            Gallery.objects.filter(is_primary=True).exclude(pk=self.instance.pk).update(is_primary=False)
        return cleaned


@admin.register(Gallery)
class GalleryAdmin(TranslatableNameAdminMixin, ModelAdminUnfoldBase):
    sidebar_icon = "storefront"
    form = GalleryAdminForm
    inlines = [GalleryTranslationInline, ArtworkGalleryInline]
    search_fields = ["slug", "translations__name", "translations__description"]
    list_filter = [
        "is_active",
        ("curator", RelatedOnlyFieldListFilter),
        has_related_filter("artwork_links", "obras", "has_artworks"),
    ]
    fieldsets = (
        ("Información básica", {
            "fields": ("curator", "logo", "is_primary")
        }),
        ("Información del sistema", {
            "fields": ("slug", "is_active")
        }),
    )
    list_display = ["display_name", "slug", "curator", "display_is_primary", "display_active"]
    list_filter = [
        "is_active",
        "is_primary",
        ("curator", RelatedOnlyFieldListFilter),
        has_related_filter("artwork_links", "obras", "has_artworks"),
    ]

    @admin.display(description="Activo", ordering="is_active", boolean=True)
    def display_active(self, obj):
        return obj.is_active

    @admin.display(description="Principal", ordering="is_primary", boolean=True)
    def display_is_primary(self, obj):
        return obj.is_primary


class ArtworkTranslationInline(TranslationInline):
    model = ArtworkTranslation
    fields = ["language", "title", "description"]


class ArtworkImageInline(TabularInline):
    model = ArtworkImage
    fields = ["image", "display_preview", "alt_es", "alt_en", "is_primary"]
    readonly_fields = ["display_preview"]
    ordering_field = "sort_order"
    hide_ordering_field = True
    extra = 0

    @admin.display(description="Vista previa")
    def display_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" class="img-preview" />', obj.image.url)
        return "-"


@admin.register(Artwork)
class ArtworkAdmin(ModelAdminUnfoldBase):
    sidebar_icon = "palette"
    inlines = [ArtworkTranslationInline, ArtworkImageInline, GalleryArtworkInline]
    search_fields = [
        "slug",
        "translations__title",
        "artist__name",
        "disciplines__translations__name",
        "techniques__translations__name",
        "themes__translations__name",
        "formats__translations__name",
        "scales__translations__name",
    ]
    list_filter = [
        "status",
        "is_active",
        "is_highlighted",
        "created_at",
        ("artist", RelatedOnlyFieldListFilter),
        ("gallery_links__gallery", RelatedOnlyFieldListFilter),
        YearFilter,
        ("disciplines", RelatedOnlyFieldListFilter),
        ("techniques", RelatedOnlyFieldListFilter),
        ("themes", RelatedOnlyFieldListFilter),
        ("formats", RelatedOnlyFieldListFilter),
        ("scales", RelatedOnlyFieldListFilter),
    ]
    autocomplete_fields = ["disciplines", "techniques", "themes", "formats", "scales"]
    list_per_page = 25
    fieldsets = (
        ("Atributos principales", {
            "fields": (("artist", "year"), "dimensions")
        }),
        ("Taxonomías", {
            "fields": (
                "disciplines",
                "techniques",
                "themes",
                "formats",
                "scales",
            )
        }),
        ("Comercial y estado", {
            "fields": (("price_mxn", "price_usd"), "status", ("is_highlighted", "views_count"))
        }),
        ("Configuración del sistema", {
            "fields": ("slug", "is_active")
        }),
    )
    list_display = [
        "display_image",
        "display_title",
        "artist",
        "display_taxonomies",
        "display_price",
        "status",
        "is_highlighted",
        "views_count",
        "display_active",
    ]

    def get_queryset(self, request):
        return (
            super().get_queryset(request)
            .prefetch_related(
                "images",
                "translations",
                "disciplines__translations",
                "techniques__translations",
                "themes__translations",
                "formats__translations",
                "scales__translations",
            )
        )

    @admin.display(description="Imagen")
    def display_image(self, obj):
        images = list(obj.images.all())
        img = next((i for i in images if i.is_primary), None) or (images[0] if images else None)
        if img and img.image:
            return format_html('<img src="{}" class="img-preview img-preview--sm" />', img.image.url)
        return "-"

    @admin.display(description="Título")
    def display_title(self, obj):
        translations = list(obj.translations.all())
        es = next((t for t in translations if t.language == "es"), None)
        if es:
            return es.title
        return translations[0].title if translations else "-"

    @admin.display(description="Clasificación")
    def display_taxonomies(self, obj):
        labels = []
        for name in ("disciplines", "techniques", "themes", "formats", "scales"):
            values = list(getattr(obj, name).all())
            if values:
                names = []
                for v in values:
                    translations = list(v.translations.all())
                    es = next((t for t in translations if t.language == "es"), None)
                    t = es or (translations[0] if translations else None)
                    if t:
                        names.append(t.name)
                if names:
                    labels.append(", ".join(names))
        return ", ".join(labels) or "-"

    @admin.display(description="Precio")
    def display_price(self, obj):
        return f"${obj.price_mxn:,.2f} MXN / ${obj.price_usd:,.2f} USD"

    @admin.display(description="Activo", ordering="is_active", boolean=True)
    def display_active(self, obj):
        return obj.is_active
