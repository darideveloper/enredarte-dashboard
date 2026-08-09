from django.conf import settings
from django.contrib import admin
from django.db.models import Max
from django.forms.models import BaseInlineFormSet
from django.utils.html import format_html, format_html_join

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
from project.admin_base import ModelAdminUnfoldBase
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


class ArtistTranslationInline(StackedInline):
    model = ArtistTranslation
    formset = TranslationInlineFormSet
    verbose_name = "Traducción"
    verbose_name_plural = "Traducciones (Español / Inglés)"
    max_num = len(settings.LANGUAGES)
    fields = ["language", "bio"]

    def get_extra(self, request, obj=None, **kwargs):
        if obj:
            existing_count = obj.translations.count()
            return max(0, len(settings.LANGUAGES) - existing_count)
        return len(settings.LANGUAGES)


class ArtistSocialLinkInline(TabularInline):
    model = ArtistSocialLink
    fields = ["platform", "url"]
    verbose_name = "Red social"
    verbose_name_plural = "Redes sociales"
    ordering_field = "sort_order"
    hide_ordering_field = True
    extra = 1


class ArtCuratorTranslationInline(StackedInline):
    model = ArtCuratorTranslation
    formset = TranslationInlineFormSet
    verbose_name = "Traducción"
    verbose_name_plural = "Traducciones (Español / Inglés)"
    max_num = len(settings.LANGUAGES)
    fields = ["language", "bio"]

    def get_extra(self, request, obj=None, **kwargs):
        if obj:
            existing_count = obj.translations.count()
            return max(0, len(settings.LANGUAGES) - existing_count)
        return len(settings.LANGUAGES)


class DisciplineTranslationInline(StackedInline):
    model = DisciplineTranslation
    formset = TranslationInlineFormSet
    verbose_name = "Traducción"
    verbose_name_plural = "Traducciones (Español / Inglés)"
    max_num = len(settings.LANGUAGES)
    fields = ["language", "name"]

    def get_extra(self, request, obj=None, **kwargs):
        if obj:
            existing_count = obj.translations.count()
            return max(0, len(settings.LANGUAGES) - existing_count)
        return len(settings.LANGUAGES)


class TechniqueTranslationInline(StackedInline):
    model = TechniqueTranslation
    formset = TranslationInlineFormSet
    verbose_name = "Traducción"
    verbose_name_plural = "Traducciones (Español / Inglés)"
    max_num = len(settings.LANGUAGES)
    fields = ["language", "name"]

    def get_extra(self, request, obj=None, **kwargs):
        if obj:
            existing_count = obj.translations.count()
            return max(0, len(settings.LANGUAGES) - existing_count)
        return len(settings.LANGUAGES)


class ThemeTranslationInline(StackedInline):
    model = ThemeTranslation
    formset = TranslationInlineFormSet
    verbose_name = "Traducción"
    verbose_name_plural = "Traducciones (Español / Inglés)"
    max_num = len(settings.LANGUAGES)
    fields = ["language", "name"]

    def get_extra(self, request, obj=None, **kwargs):
        if obj:
            existing_count = obj.translations.count()
            return max(0, len(settings.LANGUAGES) - existing_count)
        return len(settings.LANGUAGES)


class FormatTranslationInline(StackedInline):
    model = FormatTranslation
    formset = TranslationInlineFormSet
    verbose_name = "Traducción"
    verbose_name_plural = "Traducciones (Español / Inglés)"
    max_num = len(settings.LANGUAGES)
    fields = ["language", "name"]

    def get_extra(self, request, obj=None, **kwargs):
        if obj:
            existing_count = obj.translations.count()
            return max(0, len(settings.LANGUAGES) - existing_count)
        return len(settings.LANGUAGES)


class ScaleTranslationInline(StackedInline):
    model = ScaleTranslation
    formset = TranslationInlineFormSet
    verbose_name = "Traducción"
    verbose_name_plural = "Traducciones (Español / Inglés)"
    max_num = len(settings.LANGUAGES)
    fields = ["language", "name"]

    def get_extra(self, request, obj=None, **kwargs):
        if obj:
            existing_count = obj.translations.count()
            return max(0, len(settings.LANGUAGES) - existing_count)
        return len(settings.LANGUAGES)


class GalleryTranslationInline(StackedInline):
    model = GalleryTranslation
    formset = TranslationInlineFormSet
    verbose_name = "Traducción"
    verbose_name_plural = "Traducciones (Español / Inglés)"
    max_num = len(settings.LANGUAGES)
    fields = ["language", "name", "description"]

    def get_extra(self, request, obj=None, **kwargs):
        if obj:
            existing_count = obj.translations.count()
            return max(0, len(settings.LANGUAGES) - existing_count)
        return len(settings.LANGUAGES)


class LocationTranslationInline(StackedInline):
    model = LocationTranslation
    formset = TranslationInlineFormSet
    verbose_name = "Traducción"
    verbose_name_plural = "Traducciones (Español / Inglés)"
    max_num = len(settings.LANGUAGES)
    fields = ["language", "name"]

    def get_extra(self, request, obj=None, **kwargs):
        if obj:
            existing_count = obj.translations.count()
            return max(0, len(settings.LANGUAGES) - existing_count)
        return len(settings.LANGUAGES)


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


@admin.register(Artist)
class ArtistAdmin(ModelAdminUnfoldBase):
    sidebar_icon = "palette"
    inlines = [ArtistTranslationInline, ArtistSocialLinkInline]
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ["name", "email", "slug", "translations__bio"]
    list_filter = ["is_active"]
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
            "fields": (("is_active", "sort_order"),)
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
        return obj.artworks.filter(is_active=True).count()

    @admin.display(description="Disponibles")
    def display_available_count(self, obj):
        return obj.available_artworks.count()

    @admin.display(description="Técnicas")
    def display_techniques_count(self, obj):
        return obj.techniques.count()

    @admin.display(description="Destacadas")
    def display_highlighted_count(self, obj):
        return obj.highlighted_artworks.count()

    @admin.display(description="Galerías")
    def display_galleries_count(self, obj):
        return obj.curations.count()

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
    list_filter = ["is_active"]
    fieldsets = (
        ("Datos personales", {
            "fields": (("name", "slug"),)
        }),
        ("Contacto y medios", {
            "fields": ("email", "website", "photo")
        }),
        ("Estado del sistema", {
            "fields": (("is_active", "sort_order"),)
        }),
    )
    list_display = [
        "display_name",
        "display_email",
        "display_active",
        "sort_order",
    ]

    def get_changeform_initial_data(self, request):
        initial = super().get_changeform_initial_data(request)
        max_order = ArtCurator.objects.aggregate(Max("sort_order"))["sort_order__max"] or 0
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


@admin.register(Discipline)
class DisciplineAdmin(ModelAdminUnfoldBase):
    sidebar_icon = "label"
    inlines = [DisciplineTranslationInline]
    search_fields = ["slug", "translations__name"]
    list_filter = ["is_active"]
    fieldsets = (
        ("Información del sistema", {
            "fields": ("slug", "is_active", "sort_order")
        }),
    )
    list_display = ["display_name", "slug", "display_active", "sort_order"]

    def get_changeform_initial_data(self, request):
        initial = super().get_changeform_initial_data(request)
        max_order = Discipline.objects.aggregate(Max("sort_order"))["sort_order__max"] or 0
        initial["sort_order"] = max_order + 1
        return initial

    @admin.display(description="Nombre")
    def display_name(self, obj):
        es = obj.translations.filter(language="es").first()
        if es:
            return es.name
        first = obj.translations.first()
        return first.name if first else "-"

    @admin.display(description="Activo", ordering="is_active", boolean=True)
    def display_active(self, obj):
        return obj.is_active


@admin.register(Technique)
class TechniqueAdmin(ModelAdminUnfoldBase):
    sidebar_icon = "brush"
    inlines = [TechniqueTranslationInline]
    search_fields = ["slug", "translations__name"]
    list_filter = ["is_active"]
    fieldsets = (
        ("Información del sistema", {
            "fields": ("slug", "is_active", "sort_order")
        }),
    )
    list_display = ["display_name", "slug", "display_active", "sort_order"]

    def get_changeform_initial_data(self, request):
        initial = super().get_changeform_initial_data(request)
        max_order = Technique.objects.aggregate(Max("sort_order"))["sort_order__max"] or 0
        initial["sort_order"] = max_order + 1
        return initial

    @admin.display(description="Nombre")
    def display_name(self, obj):
        es = obj.translations.filter(language="es").first()
        if es:
            return es.name
        first = obj.translations.first()
        return first.name if first else "-"

    @admin.display(description="Activo", ordering="is_active", boolean=True)
    def display_active(self, obj):
        return obj.is_active


@admin.register(Theme)
class ThemeAdmin(ModelAdminUnfoldBase):
    sidebar_icon = "topic"
    inlines = [ThemeTranslationInline]
    search_fields = ["slug", "translations__name"]
    list_filter = ["is_active"]
    fieldsets = (
        ("Información del sistema", {
            "fields": ("slug", "is_active", "sort_order")
        }),
    )
    list_display = ["display_name", "slug", "display_active", "sort_order"]

    def get_changeform_initial_data(self, request):
        initial = super().get_changeform_initial_data(request)
        max_order = Theme.objects.aggregate(Max("sort_order"))["sort_order__max"] or 0
        initial["sort_order"] = max_order + 1
        return initial

    @admin.display(description="Nombre")
    def display_name(self, obj):
        es = obj.translations.filter(language="es").first()
        if es:
            return es.name
        first = obj.translations.first()
        return first.name if first else "-"

    @admin.display(description="Activo", ordering="is_active", boolean=True)
    def display_active(self, obj):
        return obj.is_active


@admin.register(Format)
class FormatAdmin(ModelAdminUnfoldBase):
    sidebar_icon = "view_module"
    inlines = [FormatTranslationInline]
    search_fields = ["slug", "translations__name"]
    list_filter = ["is_active"]
    fieldsets = (
        ("Información del sistema", {
            "fields": ("slug", "is_active", "sort_order")
        }),
    )
    list_display = ["display_name", "slug", "display_active", "sort_order"]

    def get_changeform_initial_data(self, request):
        initial = super().get_changeform_initial_data(request)
        max_order = Format.objects.aggregate(Max("sort_order"))["sort_order__max"] or 0
        initial["sort_order"] = max_order + 1
        return initial

    @admin.display(description="Nombre")
    def display_name(self, obj):
        es = obj.translations.filter(language="es").first()
        if es:
            return es.name
        first = obj.translations.first()
        return first.name if first else "-"

    @admin.display(description="Activo", ordering="is_active", boolean=True)
    def display_active(self, obj):
        return obj.is_active


@admin.register(Scale)
class ScaleAdmin(ModelAdminUnfoldBase):
    sidebar_icon = "straighten"
    inlines = [ScaleTranslationInline]
    search_fields = ["slug", "translations__name"]
    list_filter = ["is_active"]
    fieldsets = (
        ("Información del sistema", {
            "fields": ("slug", "is_active", "sort_order")
        }),
    )
    list_display = ["display_name", "slug", "display_active", "sort_order"]

    def get_changeform_initial_data(self, request):
        initial = super().get_changeform_initial_data(request)
        max_order = Scale.objects.aggregate(Max("sort_order"))["sort_order__max"] or 0
        initial["sort_order"] = max_order + 1
        return initial

    @admin.display(description="Nombre")
    def display_name(self, obj):
        es = obj.translations.filter(language="es").first()
        if es:
            return es.name
        first = obj.translations.first()
        return first.name if first else "-"

    @admin.display(description="Activo", ordering="is_active", boolean=True)
    def display_active(self, obj):
        return obj.is_active


@admin.register(Location)
class LocationAdmin(ModelAdminUnfoldBase):
    sidebar_icon = "location_on"
    inlines = [LocationTranslationInline]
    search_fields = ["slug", "translations__name"]
    list_filter = ["is_active"]
    fieldsets = (
        ("Información del sistema", {
            "fields": ("slug", "is_active", "sort_order")
        }),
    )
    list_display = ["display_name", "slug", "display_active", "sort_order"]

    def get_changeform_initial_data(self, request):
        initial = super().get_changeform_initial_data(request)
        max_order = Location.objects.aggregate(Max("sort_order"))["sort_order__max"] or 0
        initial["sort_order"] = max_order + 1
        return initial

    @admin.display(description="Nombre")
    def display_name(self, obj):
        es = obj.translations.filter(language="es").first()
        if es:
            return es.name
        first = obj.translations.first()
        return first.name if first else "-"

    @admin.display(description="Activo", ordering="is_active", boolean=True)
    def display_active(self, obj):
        return obj.is_active


@admin.register(Gallery)
class GalleryAdmin(ModelAdminUnfoldBase):
    sidebar_icon = "storefront"
    inlines = [GalleryTranslationInline, ArtworkGalleryInline]
    search_fields = ["slug", "translations__name", "translations__description"]
    list_filter = ["is_active"]
    fieldsets = (
        ("Información básica", {
            "fields": ("curator", "logo")
        }),
        ("Información del sistema", {
            "fields": ("slug", "is_active", "sort_order")
        }),
    )
    list_display = ["display_name", "slug", "curator", "display_active", "sort_order"]

    def get_changeform_initial_data(self, request):
        initial = super().get_changeform_initial_data(request)
        max_order = Gallery.objects.aggregate(Max("sort_order"))["sort_order__max"] or 0
        initial["sort_order"] = max_order + 1
        return initial

    @admin.display(description="Nombre")
    def display_name(self, obj):
        es = obj.translations.filter(language="es").first()
        if es:
            return es.name
        first = obj.translations.first()
        return first.name if first else "-"

    @admin.display(description="Activo", ordering="is_active", boolean=True)
    def display_active(self, obj):
        return obj.is_active


class ArtworkTranslationInline(StackedInline):
    model = ArtworkTranslation
    formset = TranslationInlineFormSet
    verbose_name = "Traducción"
    verbose_name_plural = "Traducciones (Español / Inglés)"
    max_num = len(settings.LANGUAGES)
    fields = ["language", "title", "description"]

    def get_extra(self, request, obj=None, **kwargs):
        if obj:
            existing_count = obj.translations.count()
            return max(0, len(settings.LANGUAGES) - existing_count)
        return len(settings.LANGUAGES)


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
            return format_html('<img src="{}" class="img-preview" style="height: 50px; border-radius: 6px;" />', obj.image.url)
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
        "disciplines",
        "techniques",
        "themes",
        "formats",
        "scales",
    ]
    filter_horizontal = ["disciplines", "techniques", "themes", "formats", "scales"]
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
            "fields": ("slug", "is_active", "sort_order")
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
        "sort_order",
    ]

    def get_changeform_initial_data(self, request):
        initial = super().get_changeform_initial_data(request)
        max_order = Artwork.objects.aggregate(Max("sort_order"))["sort_order__max"] or 0
        initial["sort_order"] = max_order + 1
        return initial

    @admin.display(description="Imagen")
    def display_image(self, obj):
        primary = obj.images.filter(is_primary=True).first() or obj.images.first()
        if primary and primary.image:
            return format_html('<img src="{}" class="img-preview" style="height: 40px; width: 40px; object-fit: cover; border-radius: 6px;" />', primary.image.url)
        return "-"

    @admin.display(description="Título")
    def display_title(self, obj):
        es = obj.translations.filter(language="es").first()
        if es:
            return es.title
        first = obj.translations.first()
        return first.title if first else "-"

    @admin.display(description="Clasificación")
    def display_taxonomies(self, obj):
        labels = []
        for name in ("disciplines", "techniques", "themes", "formats", "scales"):
            values = getattr(obj, name).all()
            if values:
                names = [v.translations.filter(language="es").first() or v.translations.first() for v in values]
                labels.append(", ".join(n.name for n in names if n))
        return ", ".join(labels) or "-"

    @admin.display(description="Precio")
    def display_price(self, obj):
        return f"${obj.price_mxn:,.2f} MXN / ${obj.price_usd:,.2f} USD"

    @admin.display(description="Activo", ordering="is_active", boolean=True)
    def display_active(self, obj):
        return obj.is_active
