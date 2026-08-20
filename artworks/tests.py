import base64

from django.contrib import admin
from django.contrib.admin import RelatedOnlyFieldListFilter
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.db import IntegrityError
from django.test import RequestFactory, TestCase
from django.urls import reverse

from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient, APITestCase

from core.models import unique_slugify

from artworks.admin import (
    ArtistAvailableWorksFilter,
    ArtCuratorAdmin,
    ArtCuratorTranslationInline,
    ArtistAdmin,
    ArtistSocialLinkInline,
    ArtistTranslationInline,
    ArtworkAdmin,
    ArtworkGalleryInline,
    ArtworkImageInline,
    ArtworkTranslationInline,
    DisciplineAdmin,
    DisciplineTranslationInline,
    FormatAdmin,
    FormatTranslationInline,
    GalleryAdmin,
    GalleryArtworkInline,
    GalleryTranslationInline,
    LocationAdmin,
    LocationTranslationInline,
    ScaleAdmin,
    ScaleTranslationInline,
    TechniqueAdmin,
    TechniqueTranslationInline,
    ThemeAdmin,
    ThemeTranslationInline,
)
from artworks.admin_filters import HasRelatedFilter, YearFilter, has_related_filter
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

_1PX_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
)


class ArtistAdminTestCase(TestCase):
    def setUp(self):
        self.superuser = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="password123"
        )
        self.client.login(username="admin", password="password123")

    def test_artist_registered_in_admin(self):
        self.assertIn(Artist, admin.site._registry)
        self.assertIsInstance(admin.site._registry[Artist], ArtistAdmin)

    def test_artist_admin_has_translation_inline(self):
        artist_admin = admin.site._registry[Artist]
        self.assertIn(ArtistTranslationInline, artist_admin.inlines)

    def test_artist_admin_changelist_view(self):
        artist = Artist.objects.create(
            name="Frida Kahlo", slug="frida-kahlo", email="frida@example.com"
        )
        ArtistTranslation.objects.create(artist=artist, language="es", bio="Pintora mexicana.")
        ArtistTranslation.objects.create(artist=artist, language="en", bio="Mexican painter.")

        url = reverse("admin:artworks_artist_changelist")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Frida Kahlo")

    def test_artist_admin_change_view(self):
        artist = Artist.objects.create(
            name="Frida Kahlo", slug="frida-kahlo", email="frida@example.com"
        )
        url = reverse("admin:artworks_artist_change", args=[artist.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Traducciones")

    def test_new_artist_add_view_initial_languages(self):
        url = reverse("admin:artworks_artist_add")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        formset = response.context_data["inline_admin_formsets"][0].formset
        self.assertEqual(len(formset.extra_forms), 2)
        self.assertEqual(formset.extra_forms[0].initial.get("language"), "es")
        self.assertEqual(formset.extra_forms[1].initial.get("language"), "en")

    def test_existing_artist_with_two_translations_has_zero_extra_forms(self):
        artist = Artist.objects.create(
            name="Diego Rivera", slug="diego-rivera", email="diego@example.com"
        )
        ArtistTranslation.objects.create(artist=artist, language="es", bio="Muralista mexicano.")
        ArtistTranslation.objects.create(artist=artist, language="en", bio="Mexican muralist.")

        url = reverse("admin:artworks_artist_change", args=[artist.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        formset = response.context_data["inline_admin_formsets"][0].formset
        self.assertEqual(len(formset.extra_forms), 0)
        self.assertEqual(len(formset.forms), 2)

class ArtCuratorAdminTestCase(TestCase):
    def setUp(self):
        self.superuser = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="password123"
        )
        self.client.login(username="admin", password="password123")

    def test_curator_registered_in_admin(self):
        self.assertIn(ArtCurator, admin.site._registry)
        self.assertIsInstance(admin.site._registry[ArtCurator], ArtCuratorAdmin)

    def test_curator_admin_has_translation_inline(self):
        curator_admin = admin.site._registry[ArtCurator]
        self.assertIn(ArtCuratorTranslationInline, curator_admin.inlines)

    def test_curator_admin_changelist_view(self):
        curator = ArtCurator.objects.create(
            name="Hans Ulrich Obrist", slug="hans-ulrich-obrist", email="hans@example.com"
        )
        ArtCuratorTranslation.objects.create(art_curator=curator, language="es", bio="Curador suizo.")
        ArtCuratorTranslation.objects.create(art_curator=curator, language="en", bio="Swiss curator.")

        url = reverse("admin:artworks_artcurator_changelist")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Hans Ulrich Obrist")

    def test_new_curator_add_view_initial_languages(self):
        url = reverse("admin:artworks_artcurator_add")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        formset = response.context_data["inline_admin_formsets"][0].formset
        self.assertEqual(len(formset.extra_forms), 2)
        self.assertEqual(formset.extra_forms[0].initial.get("language"), "es")
        self.assertEqual(formset.extra_forms[1].initial.get("language"), "en")




class TaxonomyAdminMixin:
    model = None
    admin_class = None
    translation_model = None
    translation_field = None
    translation_inline = None
    changelist_label = ""

    def setUp(self):
        self.superuser = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="password123"
        )
        self.client.login(username="admin", password="password123")

    def test_registered_in_admin(self):
        self.assertIn(self.model, admin.site._registry)
        self.assertIsInstance(admin.site._registry[self.model], self.admin_class)

    def test_has_translation_inline(self):
        model_admin = admin.site._registry[self.model]
        self.assertIn(self.translation_inline, model_admin.inlines)

    def test_changelist_view(self):
        obj = self.model.objects.create(slug="sample")
        self.translation_model.objects.create(
            **{self.translation_field: obj}, language="es", name="Muestra"
        )

        url = reverse(f"admin:artworks_{self.changelist_label}_changelist")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Muestra")

    def test_new_add_view_initial_languages(self):
        url = reverse(f"admin:artworks_{self.changelist_label}_add")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        formset = response.context_data["inline_admin_formsets"][0].formset
        self.assertEqual(len(formset.extra_forms), 2)
        self.assertEqual(formset.extra_forms[0].initial.get("language"), "es")
        self.assertEqual(formset.extra_forms[1].initial.get("language"), "en")


class DisciplineAdminTestCase(TaxonomyAdminMixin, TestCase):
    model = Discipline
    admin_class = DisciplineAdmin
    translation_model = DisciplineTranslation
    translation_field = "discipline"
    translation_inline = DisciplineTranslationInline
    changelist_label = "discipline"


class TechniqueAdminTestCase(TaxonomyAdminMixin, TestCase):
    model = Technique
    admin_class = TechniqueAdmin
    translation_model = TechniqueTranslation
    translation_field = "technique"
    translation_inline = TechniqueTranslationInline
    changelist_label = "technique"


class ThemeAdminTestCase(TaxonomyAdminMixin, TestCase):
    model = Theme
    admin_class = ThemeAdmin
    translation_model = ThemeTranslation
    translation_field = "theme"
    translation_inline = ThemeTranslationInline
    changelist_label = "theme"


class FormatAdminTestCase(TaxonomyAdminMixin, TestCase):
    model = Format
    admin_class = FormatAdmin
    translation_model = FormatTranslation
    translation_field = "format"
    translation_inline = FormatTranslationInline
    changelist_label = "format"


class ScaleAdminTestCase(TaxonomyAdminMixin, TestCase):
    model = Scale
    admin_class = ScaleAdmin
    translation_model = ScaleTranslation
    translation_field = "scale"
    translation_inline = ScaleTranslationInline
    changelist_label = "scale"


class GalleryAdminTestCase(TestCase):
    def setUp(self):
        self.superuser = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="password123"
        )
        self.client.login(username="admin", password="password123")

        self.gallery = Gallery.objects.create(slug="galeria-de-arte")
        self.gallery_admin = admin.site._registry[Gallery]

    def test_gallery_registered(self):
        """Test Gallery is registered with GalleryAdmin"""
        self.assertIn(Gallery, admin.site._registry)
        self.assertIsInstance(admin.site._registry[Gallery], GalleryAdmin)

    def test_gallery_inlines(self):
        """Test GalleryAdmin uses GalleryTranslationInline and ArtworkGalleryInline"""
        self.assertIn(GalleryTranslationInline, self.gallery_admin.inlines)
        self.assertIn(ArtworkGalleryInline, self.gallery_admin.inlines)

    def test_gallery_display_name_spanish(self):
        """Test display_name prefers Spanish translation"""
        GalleryTranslation.objects.create(
            gallery=self.gallery, language="en", name="Art Gallery"
        )
        GalleryTranslation.objects.create(
            gallery=self.gallery, language="es", name="Galería de Arte"
        )
        self.assertEqual(self.gallery_admin.display_name(self.gallery), "Galería de Arte")

    def test_gallery_display_name_fallback(self):
        """Test display_name falls back to available language if Spanish missing"""
        GalleryTranslation.objects.create(
            gallery=self.gallery, language="en", name="Art Gallery"
        )
        self.assertEqual(self.gallery_admin.display_name(self.gallery), "Art Gallery")

    def test_gallery_display_name_fallback_empty(self):
        """Test fallback when no translations exist"""
        self.assertEqual(self.gallery_admin.display_name(self.gallery), "-")

    def test_gallery_form_has_is_primary(self):
        url = reverse("admin:artworks_gallery_add")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        form = response.context_data["adminform"].form
        self.assertIn("is_primary", form.fields)

    def test_gallery_changelist_columns_and_filter_is_primary(self):
        self.assertIn("display_is_primary", self.gallery_admin.list_display)
        self.assertIn("is_primary", self.gallery_admin.list_filter)

    def test_gallery_display_is_primary(self):
        self.assertFalse(self.gallery_admin.display_is_primary(self.gallery))
        self.gallery.is_primary = True
        self.gallery.save()
        self.assertTrue(self.gallery_admin.display_is_primary(self.gallery))


class ArtworkAdminTestCase(TestCase):
    def setUp(self):
        self.superuser = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="password123"
        )
        self.client.login(username="admin", password="password123")

        call_command("base_loaddata")

        self.artist = Artist.objects.create(name="Frida Kahlo", slug="frida-kahlo")
        self.discipline = Discipline.objects.get(slug="pintura")
        self.technique = Technique.objects.get(slug="oleo")
        self.theme_feminismo = Theme.objects.get(slug="feminismo")
        self.theme_memoria = Theme.objects.get(slug="memoria")
        self.format = Format.objects.get(slug="obra-original")
        self.scale = Scale.objects.get(slug="gran-formato")

        self.artwork = Artwork.objects.create(
            artist=self.artist,
            year=1939,
            dimensions="143x152 cm",
            price_mxn=50000.00,
            price_usd=2500.00,
            status=ArtworkStatus.AVAILABLE,
            slug="las-dos-fridas",
        )
        self.artwork.disciplines.set([self.discipline])
        self.artwork.techniques.set([self.technique])
        self.artwork.themes.set([self.theme_feminismo, self.theme_memoria])
        self.artwork.formats.set([self.format])
        self.artwork.scales.set([self.scale])
        self.artwork_admin = admin.site._registry[Artwork]

    def test_artwork_registered(self):
        """Test Artwork is registered with ArtworkAdmin"""
        self.assertIn(Artwork, admin.site._registry)
        self.assertIsInstance(admin.site._registry[Artwork], ArtworkAdmin)

    def test_artwork_inlines(self):
        """Test ArtworkAdmin uses translation, image, and gallery inlines"""
        self.assertIn(ArtworkTranslationInline, self.artwork_admin.inlines)
        self.assertIn(ArtworkImageInline, self.artwork_admin.inlines)
        self.assertIn(GalleryArtworkInline, self.artwork_admin.inlines)

    def test_artwork_display_title_spanish(self):
        """Test display_title prefers Spanish translation"""
        ArtworkTranslation.objects.create(
            artwork=self.artwork, language="en", title="The Two Fridas"
        )
        ArtworkTranslation.objects.create(
            artwork=self.artwork, language="es", title="Las Dos Fridas"
        )
        self.assertEqual(self.artwork_admin.display_title(self.artwork), "Las Dos Fridas")

    def test_artwork_display_title_fallback(self):
        """Test display_title falls back to available language if Spanish missing"""
        ArtworkTranslation.objects.create(
            artwork=self.artwork, language="en", title="The Two Fridas"
        )
        self.assertEqual(self.artwork_admin.display_title(self.artwork), "The Two Fridas")

    def test_artwork_display_title_fallback_empty(self):
        """Test fallback when no translations exist"""
        self.assertEqual(self.artwork_admin.display_title(self.artwork), "-")

    def test_artwork_display_image_uses_primary(self):
        """Test display_image prefers the primary image from the prefetch cache"""
        other = ArtworkImage.objects.create(
            artwork=self.artwork,
            image=SimpleUploadedFile("other.png", _1PX_PNG),
        )
        primary = ArtworkImage.objects.create(
            artwork=self.artwork,
            image=SimpleUploadedFile("primary.png", _1PX_PNG),
            is_primary=True,
        )
        html = self.artwork_admin.display_image(self.artwork)
        self.assertIn(primary.image.url, html)
        self.assertNotIn(other.image.url, html)
        self.assertIn('class="img-preview img-preview--sm"', html)
        self.assertNotIn("style=", html)

    def test_artwork_display_image_falls_back_to_first(self):
        """Test display_image renders the first image when none is primary"""
        first = ArtworkImage.objects.create(
            artwork=self.artwork,
            image=SimpleUploadedFile("first.png", _1PX_PNG),
        )
        html = self.artwork_admin.display_image(self.artwork)
        self.assertIn(first.image.url, html)
        self.assertIn('class="img-preview img-preview--sm"', html)
        self.assertNotIn("style=", html)

    def test_artwork_display_preview_class_and_no_inline_style(self):
        """Test display_preview emits img-preview class without inline styles"""
        inline = ArtworkImageInline(ArtworkAdmin, admin.site)
        image = ArtworkImage.objects.create(
            artwork=self.artwork,
            image=SimpleUploadedFile("preview.png", _1PX_PNG),
        )
        html = inline.display_preview(image)
        self.assertIn(image.image.url, html)
        self.assertIn('class="img-preview"', html)
        self.assertNotIn("style=", html)

    def test_artwork_display_preview_fallback_empty(self):
        """Test display_preview fallback when no image is set"""
        inline = ArtworkImageInline(ArtworkAdmin, admin.site)
        image = ArtworkImage(artwork=self.artwork)
        self.assertEqual(inline.display_preview(image), "-")

    def test_artwork_display_price(self):
        """Test price formatting method"""
        self.assertEqual(
            self.artwork_admin.display_price(self.artwork),
            "$50,000.00 MXN / $2,500.00 USD"
        )

    def test_artwork_m2m_taxonomies_save(self):
        """Test an artwork can have several values per axis"""
        self.assertEqual(list(self.artwork.disciplines.all()), [self.discipline])
        self.assertEqual(
            list(self.artwork.themes.all().order_by("id")),
            [self.theme_memoria, self.theme_feminismo],
        )
        self.assertEqual(list(self.artwork.formats.all()), [self.format])
        self.assertEqual(list(self.artwork.scales.all()), [self.scale])

    def test_artwork_admin_uses_autocomplete_fields(self):
        """Test ArtworkAdmin uses autocomplete_fields for the five taxonomy M2M fields"""
        self.assertEqual(
            self.artwork_admin.autocomplete_fields,
            ["disciplines", "techniques", "themes", "formats", "scales"],
        )
        self.assertFalse(self.artwork_admin.filter_horizontal)

    def test_taxonomy_autocomplete_searches_translated_name(self):
        """Test taxonomy autocomplete matches by translated name"""
        url = reverse("admin:autocomplete")
        response = self.client.get(
            url,
            {
                "app_label": "artworks",
                "model_name": "artwork",
                "field_name": "disciplines",
                "term": "Pintura",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            str(self.discipline.pk),
            [result["id"] for result in response.json()["results"]],
        )

    def test_artwork_add_form_renders_taxonomies(self):
        """Test the artwork add form renders the five taxonomy fields"""
        url = reverse("admin:artworks_artwork_add")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        form = response.context_data["adminform"].form
        for field in ("disciplines", "techniques", "themes", "formats", "scales"):
            self.assertIn(field, form.fields)

    def test_artwork_changelist_view(self):
        """Test the artwork changelist loads and shows the taxonomy summary"""
        url = reverse("admin:artworks_artwork_changelist")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_base_loaddata_seeds_taxonomies(self):
        """Test base_loaddata creates the 36 taxonomy rows"""
        self.assertEqual(Discipline.objects.count(), 6)
        self.assertEqual(Technique.objects.count(), 7)
        self.assertEqual(Theme.objects.count(), 15)
        self.assertEqual(Format.objects.count(), 6)
        self.assertEqual(Scale.objects.count(), 2)

    def test_base_loaddata_excludes_demo_content(self):
        """Test base_loaddata does not create the seed demo rows"""
        self.assertFalse(Artist.objects.filter(slug="mariana-rios").exists())
        self.assertFalse(Artwork.objects.filter(slug="memoria-silente").exists())

    def test_base_loaddata_fail_soft_on_rerun(self):
        """Test base_loaddata re-run on a populated DB prints errors and continues"""
        call_command("base_loaddata")
        call_command("base_loaddata")
        self.assertEqual(Discipline.objects.count(), 6)
        self.assertEqual(Technique.objects.count(), 7)
        self.assertEqual(Theme.objects.count(), 15)
        self.assertEqual(Format.objects.count(), 6)
        self.assertEqual(Scale.objects.count(), 2)

    def test_seed_loaddata_loads_demo_content(self):
        """Test seed_loaddata creates sample artists and artworks (run once)"""
        call_command("seed_loaddata")
        self.assertGreater(Artist.objects.count(), 0)
        self.assertGreater(Artwork.objects.count(), 0)


class SeedContentCompletenessTestCase(TestCase):
    def setUp(self):
        call_command("base_loaddata")

    def test_seed_loaddata_populates_every_business_table(self):
        """Test seed_loaddata leaves no business table empty"""
        call_command("seed_loaddata")
        self.assertGreater(ArtCurator.objects.count(), 0)
        self.assertGreater(ArtCuratorTranslation.objects.count(), 0)
        self.assertGreater(Gallery.objects.count(), 0)
        self.assertGreater(GalleryTranslation.objects.count(), 0)
        self.assertGreater(ArtworkGallery.objects.count(), 0)
        self.assertGreater(ArtworkImage.objects.count(), 0)

    def test_seed_loaddata_rerun_does_not_increase_counts(self):
        """Test seed_loaddata twice leaves row counts unchanged"""
        call_command("seed_loaddata")
        counts = {
            "ArtCurator": ArtCurator.objects.count(),
            "Gallery": Gallery.objects.count(),
            "ArtworkGallery": ArtworkGallery.objects.count(),
            "ArtworkImage": ArtworkImage.objects.count(),
        }
        call_command("seed_loaddata")
        self.assertEqual(counts["ArtCurator"], ArtCurator.objects.count())
        self.assertEqual(counts["Gallery"], Gallery.objects.count())
        self.assertEqual(counts["ArtworkGallery"], ArtworkGallery.objects.count())
        self.assertEqual(counts["ArtworkImage"], ArtworkImage.objects.count())


class ArtistSocialLinkModelTestCase(TestCase):
    def setUp(self):
        self.artist = Artist.objects.create(name="Frida Kahlo", slug="frida-kahlo")

    def test_create_link_autofills_slug(self):
        link = ArtistSocialLink.objects.create(
            artist=self.artist,
            platform=ArtistSocialLink.Platform.INSTAGRAM,
            url="https://instagram.com/frida",
        )
        self.assertEqual(link.slug, "frida-kahlo-instagram")

    def test_platform_choices(self):
        link = ArtistSocialLink(
            artist=self.artist,
            platform=ArtistSocialLink.Platform.X,
            url="https://x.com/frida",
        )
        self.assertEqual(link.platform, "x")

    def test_slug_unique_with_suffix(self):
        ArtistSocialLink.objects.create(
            artist=self.artist,
            platform=ArtistSocialLink.Platform.INSTAGRAM,
            url="https://instagram.com/frida",
        )
        second = ArtistSocialLink.objects.create(
            artist=self.artist,
            platform=ArtistSocialLink.Platform.INSTAGRAM,
            url="https://instagram.com/frida2",
        )
        self.assertEqual(second.slug, "frida-kahlo-instagram-1")

    def test_multiple_links_per_artist(self):
        ArtistSocialLink.objects.create(
            artist=self.artist,
            platform=ArtistSocialLink.Platform.INSTAGRAM,
            url="https://instagram.com/frida",
        )
        ArtistSocialLink.objects.create(
            artist=self.artist,
            platform=ArtistSocialLink.Platform.BEHANCE,
            url="https://behance.net/frida",
        )
        self.assertEqual(self.artist.social_links.count(), 2)


class LocationModelTestCase(TestCase):
    def test_location_with_bilingual_translations(self):
        location = Location.objects.create(slug="guadalajara")
        LocationTranslation.objects.create(location=location, language="es", name="Guadalajara")
        LocationTranslation.objects.create(location=location, language="en", name="Guadalajara")
        self.assertEqual(location.translations.count(), 2)
        self.assertEqual(
            location.translations.get(language="es").name, "Guadalajara"
        )

    def test_artist_location_relation(self):
        location = Location.objects.create(slug="guadalajara")
        artist = Artist.objects.create(name="Frida", slug="frida", location=location)
        self.assertEqual(artist.location, location)
        self.assertIn(artist, location.artists.all())


class ModelStrTestCase(TestCase):
    TAXONOMIES = (
        (Location, LocationTranslation, "location"),
        (Gallery, GalleryTranslation, "gallery"),
        (Discipline, DisciplineTranslation, "discipline"),
        (Technique, TechniqueTranslation, "technique"),
        (Theme, ThemeTranslation, "theme"),
        (Format, FormatTranslation, "format"),
        (Scale, ScaleTranslation, "scale"),
    )

    def test_taxonomy_prefers_spanish_translation(self):
        for model, translation_model, field in self.TAXONOMIES:
            with self.subTest(model=model.__name__):
                obj = model.objects.create(slug="muestra")
                translation_model.objects.create(**{field: obj}, language="en", name="Sample")
                translation_model.objects.create(**{field: obj}, language="es", name="Muestra")
                self.assertEqual(str(obj), "Muestra")

    def test_taxonomy_falls_back_to_non_spanish(self):
        for model, translation_model, field in self.TAXONOMIES:
            with self.subTest(model=model.__name__):
                obj = model.objects.create(slug="muestra")
                translation_model.objects.create(**{field: obj}, language="en", name="Sample")
                self.assertEqual(str(obj), "Sample")

    def test_taxonomy_falls_back_to_slug(self):
        for model, translation_model, field in self.TAXONOMIES:
            with self.subTest(model=model.__name__):
                obj = model.objects.create(slug="sin-traducir")
                self.assertEqual(str(obj), "sin-traducir")

    def test_artwork_prefers_spanish_title(self):
        artist = Artist.objects.create(name="Frida", slug="frida")
        artwork = Artwork.objects.create(
            artist=artist, year=2020, dimensions="10x10",
            price_mxn=100, price_usd=5, status=ArtworkStatus.AVAILABLE,
            slug="las-dos-fridas",
        )
        ArtworkTranslation.objects.create(artwork=artwork, language="en", title="The Two Fridas")
        ArtworkTranslation.objects.create(artwork=artwork, language="es", title="Las Dos Fridas")
        self.assertEqual(str(artwork), "Las Dos Fridas")

    def test_artwork_falls_back_to_non_spanish_title(self):
        artist = Artist.objects.create(name="Frida", slug="frida")
        artwork = Artwork.objects.create(
            artist=artist, year=2020, dimensions="10x10",
            price_mxn=100, price_usd=5, status=ArtworkStatus.AVAILABLE,
            slug="las-dos-fridas",
        )
        ArtworkTranslation.objects.create(artwork=artwork, language="en", title="The Two Fridas")
        self.assertEqual(str(artwork), "The Two Fridas")

    def test_artwork_falls_back_to_slug(self):
        artist = Artist.objects.create(name="Frida", slug="frida")
        artwork = Artwork.objects.create(
            artist=artist, year=2020, dimensions="10x10",
            price_mxn=100, price_usd=5, status=ArtworkStatus.AVAILABLE,
            slug="las-dos-fridas",
        )
        self.assertEqual(str(artwork), "las-dos-fridas")

    def test_translation_rows_render_parent_and_language(self):
        artist = Artist.objects.create(name="Frida Kahlo", slug="frida-kahlo")
        curator = ArtCurator.objects.create(name="Hans Ulrich Obrist", slug="hans")
        artwork = Artwork.objects.create(
            artist=artist, year=2020, dimensions="10x10",
            price_mxn=100, price_usd=5, status=ArtworkStatus.AVAILABLE,
            slug="las-dos-fridas",
        )
        location = Location.objects.create(slug="guadalajara")
        gallery = Gallery.objects.create(slug="galeria-arte")
        discipline = Discipline.objects.create(slug="pintura")
        technique = Technique.objects.create(slug="oleo")
        theme = Theme.objects.create(slug="feminismo")
        format_ = Format.objects.create(slug="obra-original")
        scale = Scale.objects.create(slug="gran-formato")

        cases = (
            (ArtistTranslation.objects.create(artist=artist, language="es", bio="Pintora."), artist),
            (LocationTranslation.objects.create(location=location, language="es", name="Guadalajara"), location),
            (ArtCuratorTranslation.objects.create(art_curator=curator, language="es", bio="Curador."), curator),
            (GalleryTranslation.objects.create(gallery=gallery, language="es", name="Galería de Arte"), gallery),
            (DisciplineTranslation.objects.create(discipline=discipline, language="es", name="Pintura"), discipline),
            (TechniqueTranslation.objects.create(technique=technique, language="es", name="Óleo"), technique),
            (ThemeTranslation.objects.create(theme=theme, language="es", name="Feminismo"), theme),
            (FormatTranslation.objects.create(format=format_, language="es", name="Obra original"), format_),
            (ScaleTranslation.objects.create(scale=scale, language="es", name="Gran formato"), scale),
            (ArtworkTranslation.objects.create(artwork=artwork, language="es", title="Las Dos Fridas"), artwork),
        )
        for row, parent in cases:
            with self.subTest(model=row.__class__.__name__):
                self.assertEqual(str(row), f"{parent} ({row.language})")

    def test_artist_social_link_str(self):
        artist = Artist.objects.create(name="Frida Kahlo", slug="frida-kahlo")
        link = ArtistSocialLink.objects.create(
            artist=artist,
            platform=ArtistSocialLink.Platform.INSTAGRAM,
            url="https://instagram.com/frida",
        )
        self.assertEqual(str(link), "Instagram — Frida Kahlo")

    def test_artwork_gallery_str(self):
        artist = Artist.objects.create(name="Frida", slug="frida")
        artwork = Artwork.objects.create(
            artist=artist, year=2020, dimensions="10x10",
            price_mxn=100, price_usd=5, status=ArtworkStatus.AVAILABLE,
            slug="memoria-silente",
        )
        ArtworkTranslation.objects.create(artwork=artwork, language="es", title="Memoria silente")
        gallery = Gallery.objects.create(slug="galeria-arte")
        GalleryTranslation.objects.create(gallery=gallery, language="es", name="Galería de Arte")
        link = ArtworkGallery.objects.create(artwork=artwork, gallery=gallery, slug="link-1")
        self.assertEqual(str(link), "Memoria silente en Galería de Arte")

    def test_artwork_image_str_with_alt(self):
        artist = Artist.objects.create(name="Frida", slug="frida")
        artwork = Artwork.objects.create(
            artist=artist, year=2020, dimensions="10x10",
            price_mxn=100, price_usd=5, status=ArtworkStatus.AVAILABLE,
            slug="memoria-silente",
        )
        image = ArtworkImage.objects.create(
            artwork=artwork, image="artworks/placeholder.png", alt_es="Descripción de la obra",
        )
        self.assertEqual(str(image), "Descripción de la obra")

    def test_artwork_image_str_without_alt(self):
        artist = Artist.objects.create(name="Frida", slug="frida")
        artwork = Artwork.objects.create(
            artist=artist, year=2020, dimensions="10x10",
            price_mxn=100, price_usd=5, status=ArtworkStatus.AVAILABLE,
            slug="memoria-silente",
        )
        ArtworkTranslation.objects.create(artwork=artwork, language="es", title="Memoria silente")
        image = ArtworkImage.objects.create(artwork=artwork, image="artworks/placeholder.png")
        self.assertEqual(str(image), "Imagen de Memoria silente")

    def test_artist_and_artcurator_use_name(self):
        artist = Artist.objects.create(name="Frida Kahlo", slug="frida-kahlo")
        curator = ArtCurator.objects.create(name="Hans Ulrich Obrist", slug="hans")
        self.assertEqual(str(artist), "Frida Kahlo")
        self.assertEqual(str(curator), "Hans Ulrich Obrist")


class ArtworkDiscoveryFlagsTestCase(TestCase):
    def setUp(self):
        self.artist = Artist.objects.create(name="Frida", slug="frida")

    def _artwork(self, slug="art-1", **kwargs):
        status = kwargs.pop("status", ArtworkStatus.AVAILABLE)
        return Artwork.objects.create(
            artist=self.artist,
            year=2020,
            dimensions="10x10",
            price_mxn=100,
            price_usd=5,
            status=status,
            slug=slug,
            **kwargs,
        )

    def test_is_highlighted_default_false(self):
        self.assertFalse(self._artwork().is_highlighted)

    def test_is_highlighted_flag(self):
        self.assertTrue(self._artwork(is_highlighted=True).is_highlighted)

    def test_views_count_default_zero(self):
        self.assertEqual(self._artwork().views_count, 0)

    def test_views_count_value(self):
        self.assertEqual(self._artwork(views_count=42).views_count, 42)


class GalleryPrimaryFlagModelTestCase(TestCase):
    def _gallery(self, slug, **kwargs):
        return Gallery.objects.create(slug=slug, **kwargs)

    def test_is_primary_default_false(self):
        self.assertFalse(self._gallery("galeria-1").is_primary)

    def test_is_primary_flag(self):
        self.assertTrue(self._gallery("galeria-1", is_primary=True).is_primary)

    def test_flagging_second_unflags_first(self):
        first = self._gallery("galeria-a", is_primary=True)
        second = self._gallery("galeria-b", is_primary=True)
        first.refresh_from_db()
        self.assertFalse(first.is_primary)
        self.assertTrue(second.is_primary)

    def test_db_rejects_second_primary(self):
        self._gallery("galeria-a", is_primary=True)
        with self.assertRaises(IntegrityError):
            Gallery.objects.bulk_create([Gallery(slug="galeria-b", is_primary=True)])


class ArtistDerivedFieldsTestCase(TestCase):
    def setUp(self):
        call_command("base_loaddata")
        self.artist = Artist.objects.create(name="Frida Kahlo", slug="frida-kahlo")
        self.t1 = Technique.objects.get(slug="oleo")
        self.t2 = Technique.objects.get(slug="acrilico")
        self.gallery_a = Gallery.objects.create(slug="galeria-a")
        self.gallery_b = Gallery.objects.create(slug="galeria-b")

    def _artwork(self, slug="art-1", **kwargs):
        status = kwargs.pop("status", ArtworkStatus.AVAILABLE)
        return Artwork.objects.create(
            artist=self.artist,
            year=2020,
            dimensions="10x10",
            price_mxn=100,
            price_usd=5,
            status=status,
            slug=slug,
            **kwargs,
        )

    def test_techniques_distinct(self):
        a1 = self._artwork("art-1")
        a2 = self._artwork("art-2")
        a1.techniques.set([self.t1])
        a2.techniques.set([self.t1, self.t2])
        self.assertEqual(set(self.artist.techniques), {self.t1, self.t2})

    def test_available_artworks_filters_by_status(self):
        available = self._artwork("art-avail")
        sold = self._artwork("art-sold", status=ArtworkStatus.SOLD)
        self.assertEqual(list(self.artist.available_artworks), [available])
        self.assertNotIn(sold, self.artist.available_artworks)

    def test_new_additions_newest_first(self):
        older = self._artwork("art-old")
        newer = self._artwork("art-new")
        Artwork.objects.filter(pk=newer.pk).update(created_at="2026-01-02T00:00:00Z")
        Artwork.objects.filter(pk=older.pk).update(created_at="2026-01-01T00:00:00Z")
        self.assertEqual(list(self.artist.new_additions), [newer, older])

    def test_highlighted_artworks_filters_flag(self):
        highlighted = self._artwork("art-hi", is_highlighted=True)
        normal = self._artwork("art-n")
        self.assertEqual(list(self.artist.highlighted_artworks), [highlighted])
        self.assertNotIn(normal, self.artist.highlighted_artworks)

    def test_most_viewed_orders_desc(self):
        low = self._artwork("art-low", views_count=5)
        high = self._artwork("art-high", views_count=99)
        self.assertEqual(list(self.artist.most_viewed), [high, low])

    def test_curations_distinct_galleries(self):
        a1 = self._artwork("art-1")
        a2 = self._artwork("art-2")
        ArtworkGallery.objects.create(artwork=a1, gallery=self.gallery_a, slug="link-1")
        ArtworkGallery.objects.create(artwork=a2, gallery=self.gallery_a, slug="link-2")
        ArtworkGallery.objects.create(artwork=a1, gallery=self.gallery_b, slug="link-3")
        self.assertEqual(
            list(self.artist.curations), [self.gallery_a, self.gallery_b]
        )


class LocationAdminTestCase(TaxonomyAdminMixin, TestCase):
    model = Location
    admin_class = LocationAdmin
    translation_model = LocationTranslation
    translation_field = "location"
    translation_inline = LocationTranslationInline
    changelist_label = "location"


class ArtistAdminProfileTestCase(TestCase):
    def setUp(self):
        self.superuser = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="password123"
        )
        self.client.login(username="admin", password="password123")
        call_command("base_loaddata")

        self.artist = Artist.objects.create(name="Frida Kahlo", slug="frida-kahlo")
        location = Location.objects.get(slug="guadalajara")
        Artist.objects.filter(pk=self.artist.pk).update(location=location)

        artwork = Artwork.objects.create(
            artist=self.artist,
            year=2020,
            dimensions="10x10",
            price_mxn=100,
            price_usd=5,
            status=ArtworkStatus.AVAILABLE,
            slug="art-1",
            is_highlighted=True,
            views_count=9,
        )
        artwork.techniques.set([Technique.objects.get(slug="oleo")])
        gallery = Gallery.objects.create(slug="galeria-a")
        ArtworkGallery.objects.create(artwork=artwork, gallery=gallery, slug="link-1")

        self.artist_admin = admin.site._registry[Artist]

    def test_artist_admin_has_social_links_inline(self):
        self.assertIn(ArtistSocialLinkInline, self.artist_admin.inlines)

    def test_artist_changelist_count_columns(self):
        request = RequestFactory().get("/")
        artist = self.artist_admin.get_queryset(request).get(pk=self.artist.pk)
        self.assertEqual(self.artist_admin.display_artworks_count(artist), 1)
        self.assertEqual(self.artist_admin.display_available_count(artist), 1)
        self.assertEqual(self.artist_admin.display_techniques_count(artist), 1)
        self.assertEqual(self.artist_admin.display_highlighted_count(artist), 1)
        self.assertEqual(self.artist_admin.display_galleries_count(artist), 1)

    def test_artist_count_columns_issue_no_per_row_queries(self):
        """Changelist count columns must read annotations, not query per row."""
        request = RequestFactory().get("/")
        with self.assertNumQueries(1):
            artists = list(self.artist_admin.get_queryset(request))
        with self.assertNumQueries(0):
            for artist in artists:
                for method in (
                    self.artist_admin.display_artworks_count,
                    self.artist_admin.display_available_count,
                    self.artist_admin.display_techniques_count,
                    self.artist_admin.display_highlighted_count,
                    self.artist_admin.display_galleries_count,
                ):
                    method(artist)

    def test_artist_count_annotations_handle_multi_relation_fanout(self):
        """Counts must not over-count when artworks/techniques/galleries joins fan out."""
        technique = Technique.objects.get(slug="oleo")
        gallery = Gallery.objects.create(slug="galeria-b")
        for i in range(3):
            artwork = Artwork.objects.create(
                artist=self.artist,
                year=2021,
                dimensions="10x10",
                price_mxn=100,
                price_usd=5,
                status=ArtworkStatus.AVAILABLE,
                slug=f"art-fanout-{i}",
                is_highlighted=True,
            )
            artwork.techniques.set([technique])
            ArtworkGallery.objects.create(artwork=artwork, gallery=gallery, slug=f"fl-{i}")

        request = RequestFactory().get("/")
        artist = self.artist_admin.get_queryset(request).get(pk=self.artist.pk)
        self.assertEqual(self.artist_admin.display_artworks_count(artist), 4)
        self.assertEqual(self.artist_admin.display_available_count(artist), 4)
        self.assertEqual(self.artist_admin.display_techniques_count(artist), 1)
        self.assertEqual(self.artist_admin.display_highlighted_count(artist), 4)
        self.assertEqual(self.artist_admin.display_galleries_count(artist), 2)

    def test_artist_changelist_view(self):
        url = reverse("admin:artworks_artist_changelist")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Frida Kahlo")

    def test_artist_change_view_renders_resumen(self):
        url = reverse("admin:artworks_artist_change", args=[self.artist.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Resumen")
        self.assertContains(response, "1 obra(s) disponible(s)")


class ArtworkDiscoveryAdminTestCase(TestCase):
    def setUp(self):
        self.superuser = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="password123"
        )
        self.client.login(username="admin", password="password123")
        self.artist = Artist.objects.create(name="Frida", slug="frida")
        Artwork.objects.create(
            artist=self.artist,
            year=2020,
            dimensions="10x10",
            price_mxn=100,
            price_usd=5,
            status=ArtworkStatus.AVAILABLE,
            slug="art-1",
        )
        self.artwork_admin = admin.site._registry[Artwork]

    def test_artwork_form_has_discovery_fields(self):
        url = reverse("admin:artworks_artwork_add")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        form = response.context_data["adminform"].form
        self.assertIn("is_highlighted", form.fields)
        self.assertIn("views_count", form.fields)

    def test_artwork_changelist_columns_and_filter(self):
        self.assertIn("is_highlighted", self.artwork_admin.list_display)
        self.assertIn("views_count", self.artwork_admin.list_display)
        self.assertIn("is_highlighted", self.artwork_admin.list_filter)

    def test_artwork_admin_filters(self):
        self.assertIn(("artist", RelatedOnlyFieldListFilter), self.artwork_admin.list_filter)
        self.assertIn(("gallery_links__gallery", RelatedOnlyFieldListFilter), self.artwork_admin.list_filter)
        self.assertIn(YearFilter, self.artwork_admin.list_filter)
        self.assertIn("created_at", self.artwork_admin.list_filter)
        self.assertIn(("disciplines", RelatedOnlyFieldListFilter), self.artwork_admin.list_filter)
        self.assertEqual(self.artwork_admin.list_per_page, 25)

    def test_artist_admin_filters(self):
        artist_admin = admin.site._registry[Artist]
        self.assertIn(("location", RelatedOnlyFieldListFilter), artist_admin.list_filter)
        self.assertIn("created_at", artist_admin.list_filter)
        self.assertIn(ArtistAvailableWorksFilter, artist_admin.list_filter)
        self.assertEqual(artist_admin.list_per_page, 50)

    def test_gallery_admin_filters(self):
        gallery_admin = admin.site._registry[Gallery]
        self.assertIn(("curator", RelatedOnlyFieldListFilter), gallery_admin.list_filter)

    def test_artcurator_admin_filters(self):
        artcurator_admin = admin.site._registry[ArtCurator]
        self.assertIn("is_active", artcurator_admin.list_filter)
        self.assertTrue(
            any(
                isinstance(f, type) and issubclass(f, HasRelatedFilter)
                for f in artcurator_admin.list_filter
            ),
            "ArtCuratorAdmin missing HasRelatedFilter",
        )

    def test_taxonomy_admin_in_use_filters(self):
        for admin_class in (
            DisciplineAdmin,
            TechniqueAdmin,
            ThemeAdmin,
            FormatAdmin,
            ScaleAdmin,
            LocationAdmin,
        ):
            with self.subTest(admin_class=admin_class.__name__):
                self.assertTrue(
                    any(
                        isinstance(f, type)
                        and issubclass(f, HasRelatedFilter)
                        for f in admin_class.list_filter
                    ),
                    f"{admin_class.__name__} missing HasRelatedFilter",
                )


class AdminFilterBehaviorTestCase(TestCase):
    def setUp(self):
        self.request = RequestFactory().get("/admin/")
        self.artist_admin = admin.site._registry[Artist]
        self.artwork_admin = admin.site._registry[Artwork]

    def test_has_related_filter_artists(self):
        artist_filter = has_related_filter("artworks", "obras", "test_has_artworks")
        artist_with = Artist.objects.create(name="Con obras", slug="con-obras")
        artist_without = Artist.objects.create(name="Sin obras", slug="sin-obras")
        Artwork.objects.create(
            artist=artist_with,
            year=2020,
            dimensions="10x10",
            price_mxn=100,
            price_usd=5,
            status=ArtworkStatus.AVAILABLE,
            slug="art-behavior-1",
        )

        with_filter = artist_filter(
            self.request, {"test_has_artworks": ["with"]}, Artist, self.artist_admin
        )
        result = with_filter.queryset(self.request, Artist.objects.all())
        self.assertIn(artist_with, result)
        self.assertNotIn(artist_without, result)

        without_filter = artist_filter(
            self.request, {"test_has_artworks": ["without"]}, Artist, self.artist_admin
        )
        result = without_filter.queryset(self.request, Artist.objects.all())
        self.assertIn(artist_without, result)
        self.assertNotIn(artist_with, result)

    def test_year_filter_decade(self):
        Artwork.objects.create(
            artist=Artist.objects.create(name="A", slug="a-year"),
            year=1985,
            dimensions="10x10",
            price_mxn=100,
            price_usd=5,
            status=ArtworkStatus.AVAILABLE,
            slug="art-1985",
        )
        Artwork.objects.create(
            artist=Artist.objects.create(name="B", slug="b-year"),
            year=1992,
            dimensions="10x10",
            price_mxn=100,
            price_usd=5,
            status=ArtworkStatus.AVAILABLE,
            slug="art-1992",
        )

        filter_80s = YearFilter(self.request, {"decade": ["1980"]}, Artwork, self.artwork_admin)
        result = filter_80s.queryset(self.request, Artwork.objects.all())
        self.assertEqual(set(result.values_list("year", flat=True)), {1985})

        filter_90s = YearFilter(self.request, {"decade": ["1990"]}, Artwork, self.artwork_admin)
        result = filter_90s.queryset(self.request, Artwork.objects.all())
        self.assertEqual(set(result.values_list("year", flat=True)), {1992})

    def test_year_filter_lookups_build_decades(self):
        for year in (1978, 1984, 1985, 1993):
            Artwork.objects.create(
                artist=Artist.objects.create(name=f"Y{year}", slug=f"y-{year}"),
                year=year,
                dimensions="10x10",
                price_mxn=100,
                price_usd=5,
                status=ArtworkStatus.AVAILABLE,
                slug=f"art-y-{year}",
            )
        filter_ = YearFilter(self.request, {}, Artwork, self.artwork_admin)
        lookups = filter_.lookups(self.request, self.artwork_admin)
        self.assertEqual(lookups, [("1970", "1970–1979"), ("1980", "1980–1989"), ("1990", "1990–1999")])

    def test_year_filter_lookups_empty_table(self):
        filter_ = YearFilter(self.request, {}, Artwork, self.artwork_admin)
        self.assertEqual(filter_.lookups(self.request, self.artwork_admin), [])

    def test_artist_available_works_filter(self):
        artist_available = Artist.objects.create(name="Disponible", slug="disponible")
        artist_sold = Artist.objects.create(name="Vendida", slug="vendida")
        Artwork.objects.create(
            artist=artist_available,
            year=2020,
            dimensions="10x10",
            price_mxn=100,
            price_usd=5,
            status=ArtworkStatus.AVAILABLE,
            slug="art-avail-1",
        )
        Artwork.objects.create(
            artist=artist_sold,
            year=2020,
            dimensions="10x10",
            price_mxn=100,
            price_usd=5,
            status=ArtworkStatus.SOLD,
            slug="art-sold-1",
        )

        with_filter = ArtistAvailableWorksFilter(
            self.request, {"has_available": ["with"]}, Artist, self.artist_admin
        )
        result = with_filter.queryset(self.request, Artist.objects.all())
        self.assertIn(artist_available, result)
        self.assertNotIn(artist_sold, result)

        without_filter = ArtistAvailableWorksFilter(
            self.request, {"has_available": ["without"]}, Artist, self.artist_admin
        )
        result = without_filter.queryset(self.request, Artist.objects.all())
        self.assertIn(artist_sold, result)
        self.assertNotIn(artist_available, result)


class StaticfilesBackendTestCase(TestCase):
    def test_test_suite_uses_plain_staticfiles_storage(self):
        from django.conf import settings

        self.assertEqual(
            settings.STORAGES["staticfiles"]["BACKEND"],
            "django.contrib.staticfiles.storage.StaticFilesStorage",
        )

    def test_production_staticfiles_backend_is_whitenoise(self):
        import project.settings as settings_module

        if not settings_module.IS_TESTING:
            self.assertEqual(
                settings_module.STORAGES["staticfiles"]["BACKEND"],
                "whitenoise.storage.CompressedManifestStaticFilesStorage",
            )


class TranslationInlineEnforcementTestCase(TestCase):
    ALL_TRANSLATION_INLINES = (
        ArtistTranslationInline,
        ArtCuratorTranslationInline,
        DisciplineTranslationInline,
        TechniqueTranslationInline,
        ThemeTranslationInline,
        FormatTranslationInline,
        ScaleTranslationInline,
        GalleryTranslationInline,
        LocationTranslationInline,
        ArtworkTranslationInline,
    )
    ALL_ADD_LABELS = (
        "artist",
        "artcurator",
        "discipline",
        "technique",
        "theme",
        "format",
        "scale",
        "gallery",
        "location",
        "artwork",
    )

    def setUp(self):
        self.superuser = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="password123"
        )
        self.client.login(username="admin", password="password123")

    def test_all_translation_inlines_disable_delete(self):
        for inline in self.ALL_TRANSLATION_INLINES:
            self.assertFalse(inline.can_delete, inline.__name__)

    def test_all_translation_add_views_render(self):
        for label in self.ALL_ADD_LABELS:
            response = self.client.get(reverse(f"admin:artworks_{label}_add"))
            self.assertEqual(response.status_code, 200, label)

    def test_discipline_save_with_both_languages_succeeds(self):
        response = self.client.post(
            reverse("admin:artworks_discipline_add"),
            {
                "slug": "escultura",
                "is_active": "on",
                "translations-TOTAL_FORMS": "2",
                "translations-INITIAL_FORMS": "0",
                "translations-MIN_NUM_FORMS": "0",
                "translations-MAX_NUM_FORMS": "2",
                "translations-0-language": "es",
                "translations-0-name": "Escultura",
                "translations-1-language": "en",
                "translations-1-name": "Sculpture",
            },
        )
        self.assertEqual(response.status_code, 302)
        discipline = Discipline.objects.get(slug="escultura")
        self.assertEqual(discipline.translations.count(), 2)

    def test_discipline_save_with_one_language_rejected(self):
        response = self.client.post(
            reverse("admin:artworks_discipline_add"),
            {
                "slug": "escultura",
                "is_active": "on",
                "translations-TOTAL_FORMS": "2",
                "translations-INITIAL_FORMS": "0",
                "translations-MIN_NUM_FORMS": "0",
                "translations-MAX_NUM_FORMS": "2",
                "translations-0-language": "es",
                "translations-0-name": "Escultura",
                "translations-1-language": "en",
                "translations-1-name": "",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Discipline.objects.filter(slug="escultura").exists())

    def test_curator_untouched_inline_rejected(self):
        response = self.client.post(
            reverse("admin:artworks_artcurator_add"),
            {
                "name": "Curador",
                "slug": "curador",
                "is_active": "on",
                "translations-TOTAL_FORMS": "2",
                "translations-INITIAL_FORMS": "0",
                "translations-MIN_NUM_FORMS": "0",
                "translations-MAX_NUM_FORMS": "2",
                "translations-0-language": "es",
                "translations-0-bio": "",
                "translations-1-language": "en",
                "translations-1-bio": "",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(ArtCurator.objects.filter(slug="curador").exists())

    def test_curator_legacy_single_language_blocked_on_edit(self):
        curator = ArtCurator.objects.create(name="Curador", slug="curador")
        ArtCuratorTranslation.objects.create(art_curator=curator, language="es", bio="Bio ES")
        es_row = curator.translations.get(language="es")

        response = self.client.post(
            reverse("admin:artworks_artcurator_change", args=[curator.pk]),
            {
                "name": "Curador",
                "slug": "curador",
                "is_active": "on",
                "translations-TOTAL_FORMS": "2",
                "translations-INITIAL_FORMS": "1",
                "translations-MIN_NUM_FORMS": "0",
                "translations-MAX_NUM_FORMS": "2",
                "translations-0-id": str(es_row.pk),
                "translations-0-language": "es",
                "translations-0-bio": "Bio ES",
                "translations-1-language": "en",
                "translations-1-bio": "",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(curator.translations.count(), 1)

    def test_curator_legacy_zero_languages_blocked_on_edit(self):
        curator = ArtCurator.objects.create(name="Curador", slug="curador")

        response = self.client.post(
            reverse("admin:artworks_artcurator_change", args=[curator.pk]),
            {
                "name": "Curador",
                "slug": "curador",
                "is_active": "on",
                "translations-TOTAL_FORMS": "2",
                "translations-INITIAL_FORMS": "0",
                "translations-MIN_NUM_FORMS": "0",
                "translations-MAX_NUM_FORMS": "2",
                "translations-0-language": "es",
                "translations-0-bio": "",
                "translations-1-language": "en",
                "translations-1-bio": "",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(curator.translations.count(), 0)

    def test_existing_parent_with_one_translation_shows_extra_row(self):
        curator = ArtCurator.objects.create(name="Curador", slug="curador")
        ArtCuratorTranslation.objects.create(art_curator=curator, language="es", bio="Bio ES")

        response = self.client.get(reverse("admin:artworks_artcurator_change", args=[curator.pk]))
        self.assertEqual(response.status_code, 200)
        formset = response.context_data["inline_admin_formsets"][0].formset
        self.assertEqual(len(formset.initial_forms), 1)
        self.assertEqual(len(formset.extra_forms), 1)
        self.assertEqual(formset.extra_forms[0].initial.get("language"), "en")

    def test_more_than_two_translation_rows_rejected(self):
        response = self.client.post(
            reverse("admin:artworks_discipline_add"),
            {
                "slug": "escultura",
                "is_active": "on",
                "translations-TOTAL_FORMS": "3",
                "translations-INITIAL_FORMS": "0",
                "translations-MIN_NUM_FORMS": "0",
                "translations-MAX_NUM_FORMS": "2",
                "translations-0-language": "es",
                "translations-0-name": "Escultura",
                "translations-1-language": "en",
                "translations-1-name": "Sculpture",
                "translations-2-language": "es",
                "translations-2-name": "Tercera",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Discipline.objects.filter(slug="escultura").exists())


class UniqueSlugifyTestCase(TestCase):
    def test_no_collision_returns_base(self):
        self.assertEqual(unique_slugify("pintura", Discipline.objects.all()), "pintura")

    def test_collision_appends_suffix(self):
        Discipline.objects.create(slug="oleo")
        Discipline.objects.create(slug="oleo-1")
        self.assertEqual(unique_slugify("oleo", Discipline.objects.all()), "oleo-2")

    def test_input_is_slugified(self):
        self.assertEqual(unique_slugify("Arte Abstracto", Discipline.objects.all()), "arte-abstracto")


class SlugBackfillMixinTestCase(TestCase):
    def test_orm_creation_backfills_from_es_name(self):
        discipline = Discipline.objects.create()
        DisciplineTranslation.objects.create(discipline=discipline, language="es", name="Pintura")
        self.assertEqual(discipline.slug, "pintura")

    def test_admin_creation_backfills_without_typed_slug(self):
        superuser = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="password123"
        )
        self.client.login(username="admin", password="password123")
        response = self.client.post(
            reverse("admin:artworks_discipline_add"),
            {
                "is_active": "on",
                "translations-TOTAL_FORMS": "2",
                "translations-INITIAL_FORMS": "0",
                "translations-MIN_NUM_FORMS": "0",
                "translations-MAX_NUM_FORMS": "2",
                "translations-0-language": "es",
                "translations-0-name": "Pintura",
                "translations-1-language": "en",
                "translations-1-name": "Painting",
            },
        )
        self.assertEqual(response.status_code, 302)
        discipline = Discipline.objects.latest("id")
        self.assertEqual(discipline.slug, "pintura")

    def test_colliding_translated_slugs_get_suffix(self):
        first = Discipline.objects.create()
        DisciplineTranslation.objects.create(discipline=first, language="es", name="Óleo")
        second = Discipline.objects.create()
        DisciplineTranslation.objects.create(discipline=second, language="es", name="Óleo")
        self.assertEqual(first.slug, "oleo")
        self.assertEqual(second.slug, "oleo-1")

    def test_non_es_translation_does_not_backfill(self):
        discipline = Discipline.objects.create()
        DisciplineTranslation.objects.create(discipline=discipline, language="en", name="Painting")
        self.assertEqual(discipline.slug, "")

    def test_existing_slug_is_preserved(self):
        discipline = Discipline.objects.create(slug="escultura")
        DisciplineTranslation.objects.create(discipline=discipline, language="es", name="Pintura")
        self.assertEqual(discipline.slug, "escultura")


class ArtworkCompositeSlugTestCase(TestCase):
    def setUp(self):
        self.artist = Artist.objects.create(name="Frida Kahlo", slug="frida-kahlo")

    def _artwork(self, **kwargs):
        defaults = dict(
            artist=self.artist, year=1939, dimensions="10x10",
            price_mxn=100, price_usd=5, status=ArtworkStatus.AVAILABLE,
        )
        defaults.update(kwargs)
        return Artwork.objects.create(**defaults)

    def test_composite_slug_from_artist_and_title(self):
        artwork = self._artwork()
        ArtworkTranslation.objects.create(artwork=artwork, language="es", title="Las Dos Fridas")
        self.assertEqual(artwork.slug, "frida-kahlo-las-dos-fridas")

    def test_cross_artist_titles_are_distinct(self):
        other = Artist.objects.create(name="Diego Rivera", slug="diego-rivera")
        a = self._artwork()
        ArtworkTranslation.objects.create(artwork=a, language="es", title="Las Dos Fridas")
        b = Artwork.objects.create(
            artist=other, year=1935, dimensions="10x10",
            price_mxn=100, price_usd=5, status=ArtworkStatus.AVAILABLE,
        )
        ArtworkTranslation.objects.create(artwork=b, language="es", title="Las Dos Fridas")
        self.assertEqual(a.slug, "frida-kahlo-las-dos-fridas")
        self.assertEqual(b.slug, "diego-rivera-las-dos-fridas")

    def test_same_artist_title_collision_gets_suffix(self):
        a = self._artwork()
        ArtworkTranslation.objects.create(artwork=a, language="es", title="Las Dos Fridas")
        b = self._artwork()
        ArtworkTranslation.objects.create(artwork=b, language="es", title="Las Dos Fridas")
        self.assertEqual(a.slug, "frida-kahlo-las-dos-fridas")
        self.assertEqual(b.slug, "frida-kahlo-las-dos-fridas-1")


class InlineTokenSlugTestCase(TestCase):
    def setUp(self):
        self.artist = Artist.objects.create(name="Frida Kahlo", slug="frida-kahlo")
        self.artwork = Artwork.objects.create(
            artist=self.artist, year=1939, dimensions="10x10",
            price_mxn=100, price_usd=5, status=ArtworkStatus.AVAILABLE,
            slug="las-dos-fridas",
        )
        self.gallery = Gallery.objects.create(slug="galeria-arte")

    def test_artwork_image_gets_token_slug(self):
        image = ArtworkImage.objects.create(artwork=self.artwork, image="artworks/a.png")
        self.assertTrue(image.slug)
        self.assertNotEqual(image.slug, "")

    def test_artwork_gallery_gets_token_slug(self):
        link = ArtworkGallery.objects.create(artwork=self.artwork, gallery=self.gallery)
        self.assertTrue(link.slug)
        self.assertNotEqual(link.slug, "")

    def test_multiple_images_get_distinct_slugs(self):
        first = ArtworkImage.objects.create(artwork=self.artwork, image="artworks/a.png")
        second = ArtworkImage.objects.create(artwork=self.artwork, image="artworks/b.png")
        third = ArtworkImage.objects.create(artwork=self.artwork, image="artworks/c.png")
        slugs = {first.slug, second.slug, third.slug}
        self.assertEqual(len(slugs), 3)

    def test_multiple_gallery_links_get_distinct_slugs(self):
        other = Gallery.objects.create(slug="otra-galeria")
        first = ArtworkGallery.objects.create(artwork=self.artwork, gallery=self.gallery)
        second = ArtworkGallery.objects.create(artwork=self.artwork, gallery=other)
        self.assertNotEqual(first.slug, second.slug)


class ArtworksAPITestCase(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="api-user", password="unused")
        self.token = Token.objects.create(user=self.user)

        self.location = Location.objects.create(slug="ciudad-de-mexico")
        LocationTranslation.objects.create(
            location=self.location, language="es", name="Ciudad de México"
        )
        LocationTranslation.objects.create(
            location=self.location, language="en", name="Mexico City"
        )

        self.artist = Artist.objects.create(
            name="Ana Álvarez", slug="ana-alvarez", location=self.location,
            photo=SimpleUploadedFile("ana.webp", _1PX_PNG),
        )
        ArtistTranslation.objects.create(artist=self.artist, language="es", bio="Biografía ES")
        ArtistTranslation.objects.create(artist=self.artist, language="en", bio="Bio EN")

        self.inactive_artist = Artist.objects.create(
            name="Inactiva", slug="inactiva", is_active=False
        )

        self.discipline = Discipline.objects.create(slug="pintura")
        DisciplineTranslation.objects.create(
            discipline=self.discipline, language="es", name="Pintura"
        )
        DisciplineTranslation.objects.create(
            discipline=self.discipline, language="en", name="Painting"
        )

        self.artwork = Artwork.objects.create(
            artist=self.artist,
            slug="obra-1",
            year=2024,
            dimensions="10x10",
            price_mxn=1000,
            price_usd=50,
            status=ArtworkStatus.AVAILABLE,
            is_highlighted=True,
            views_count=5,
        )
        self.artwork.disciplines.set([self.discipline])
        ArtworkTranslation.objects.create(
            artwork=self.artwork, language="es", title="Obra Uno", description="Desc ES"
        )
        ArtworkTranslation.objects.create(artwork=self.artwork, language="en", title="Work One")
        ArtworkImage.objects.create(
            artwork=self.artwork,
            image=SimpleUploadedFile("obra1.png", _1PX_PNG),
            alt_es="Alt ES",
            alt_en="Alt EN",
            is_primary=True,
            sort_order=1,
        )

    def _auth_get(self, path):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        return self.client.get(path)

    def test_anonymous_request_rejected(self):
        response = APIClient().get("/apis/artworks/artworks/")
        self.assertEqual(response.status_code, 401)

    def test_router_root_lists_all_endpoints(self):
        response = self._auth_get("/apis/artworks/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 10)

    def test_artwork_list_paginated_envelope(self):
        response = self._auth_get("/apis/artworks/artworks/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        for key in ("count", "next", "previous", "page", "page_size", "total_pages", "results"):
            self.assertIn(key, data)
        self.assertEqual(data["count"], 1)

    def test_page_size_param_respected(self):
        response = self._auth_get("/apis/artworks/artworks/?page_size=50")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["page_size"], 50)

    def test_inactive_artists_excluded(self):
        response = self._auth_get("/apis/artworks/artists/")
        self.assertEqual(response.status_code, 200)
        slugs = [a["slug"] for a in response.json()["results"]]
        self.assertIn("ana-alvarez", slugs)
        self.assertNotIn("inactiva", slugs)

    def test_artist_detail_shape(self):
        response = self._auth_get(f"/apis/artworks/artists/{self.artist.id}/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["location"], {"id": self.location.id, "slug": "ciudad-de-mexico"})
        self.assertEqual(data["translations"]["es"], {"bio": "Biografía ES"})
        self.assertEqual(data["translations"]["en"], {"bio": "Bio EN"})
        self.assertTrue(data["photo"].startswith("http"))
        self.assertNotIn("sort_order", data)

    def test_artwork_detail_shape(self):
        response = self._auth_get(f"/apis/artworks/artworks/{self.artwork.id}/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["artist"], {"id": self.artist.id, "slug": "ana-alvarez"})
        self.assertEqual(
            data["disciplines"], [{"id": self.discipline.id, "slug": "pintura"}]
        )
        self.assertEqual(data["translations"]["es"]["title"], "Obra Uno")
        self.assertIsInstance(data["price_mxn"], (int, float))
        self.assertNotIsInstance(data["price_mxn"], str)
        self.assertEqual(len(data["images"]), 1)
        self.assertTrue(data["images"][0]["image"].startswith("http"))

    def test_gallery_translation_blank_description_excluded(self):
        gallery = Gallery.objects.create(slug="galeria-x")
        GalleryTranslation.objects.create(
            gallery=gallery, language="es", name="Galería X", description=""
        )
        response = self._auth_get(f"/apis/artworks/galleries/{gallery.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["translations"], {"es": {"name": "Galería X"}})

    def test_gallery_serializer_includes_is_primary(self):
        Gallery.objects.create(slug="galeria-a", is_primary=True)
        Gallery.objects.create(slug="galeria-b")
        response = self._auth_get("/apis/artworks/galleries/")
        self.assertEqual(response.status_code, 200)
        results = response.json()["results"]
        by_slug = {g["slug"]: g for g in results}
        self.assertTrue(by_slug["galeria-a"]["is_primary"])
        self.assertFalse(by_slug["galeria-b"]["is_primary"])

    def test_404_returns_error_envelope(self):
        response = self._auth_get("/apis/artworks/artworks/9999/")
        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertEqual(data["status"], "error")
        self.assertIn("message", data)
        self.assertIn("data", data)

    def test_inactive_social_link_excluded(self):
        ArtistSocialLink.objects.create(
            artist=self.artist,
            platform=ArtistSocialLink.Platform.INSTAGRAM,
            url="https://instagram.com/ana",
        )
        ArtistSocialLink.objects.create(
            artist=self.artist,
            platform=ArtistSocialLink.Platform.X,
            url="https://x.com/ana",
            is_active=False,
        )
        response = self._auth_get(f"/apis/artworks/artists/{self.artist.id}/")
        self.assertEqual(response.status_code, 200)
        links = response.json()["social_links"]
        self.assertEqual(len(links), 1)
        self.assertEqual(links[0]["platform"], "instagram")

    def test_inactive_location_returns_null(self):
        Location.objects.filter(pk=self.location.pk).update(is_active=False)
        response = self._auth_get(f"/apis/artworks/artists/{self.artist.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.json()["location"])

    def test_inactive_curator_returns_null(self):
        curator = ArtCurator.objects.create(name="Curador", slug="curador")
        gallery = Gallery.objects.create(slug="galeria-a", curator=curator)
        ArtCurator.objects.filter(pk=curator.pk).update(is_active=False)
        response = self._auth_get(f"/apis/artworks/galleries/{gallery.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.json()["curator"])

    def test_gallery_artwork_links_exclude_inactive(self):
        gallery = Gallery.objects.create(slug="galeria-a")
        artwork2 = Artwork.objects.create(
            artist=self.artist,
            slug="obra-2",
            year=2023,
            dimensions="20x20",
            price_mxn=2000,
            price_usd=100,
            status=ArtworkStatus.AVAILABLE,
        )
        inactive_artwork = Artwork.objects.create(
            artist=self.artist,
            slug="obra-inactiva",
            year=2022,
            dimensions="15x15",
            price_mxn=500,
            price_usd=25,
            status=ArtworkStatus.AVAILABLE,
            is_active=False,
        )
        active_link = ArtworkGallery.objects.create(
            artwork=self.artwork, gallery=gallery
        )
        ArtworkGallery.objects.create(
            artwork=inactive_artwork, gallery=gallery
        )
        ArtworkGallery.objects.create(
            artwork=artwork2, gallery=gallery, is_active=False
        )
        response = self._auth_get(f"/apis/artworks/galleries/{gallery.id}/")
        self.assertEqual(response.status_code, 200)
        links = response.json()["artwork_links"]
        self.assertEqual([l["id"] for l in links], [active_link.id])

    def test_artwork_gallery_links_exclude_inactive_gallery(self):
        gallery = Gallery.objects.create(slug="galeria-a")
        inactive_gallery = Gallery.objects.create(
            slug="galeria-b", is_active=False
        )
        third_gallery = Gallery.objects.create(slug="galeria-c")
        active_link = ArtworkGallery.objects.create(
            artwork=self.artwork, gallery=gallery
        )
        ArtworkGallery.objects.create(
            artwork=self.artwork, gallery=inactive_gallery
        )
        ArtworkGallery.objects.create(
            artwork=self.artwork, gallery=third_gallery, is_active=False
        )
        response = self._auth_get(f"/apis/artworks/artworks/{self.artwork.id}/")
        self.assertEqual(response.status_code, 200)
        links = response.json()["gallery_links"]
        self.assertEqual([l["id"] for l in links], [active_link.id])

    def test_inactive_taxonomy_term_excluded(self):
        inactive = Discipline.objects.create(
            slug="escultura", is_active=False
        )
        self.artwork.disciplines.add(inactive)
        response = self._auth_get(f"/apis/artworks/artworks/{self.artwork.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["disciplines"],
            [{"id": self.discipline.id, "slug": "pintura"}],
        )

    def test_inactive_image_excluded(self):
        ArtworkImage.objects.create(
            artwork=self.artwork,
            image=SimpleUploadedFile("inactive.png", _1PX_PNG),
            is_active=False,
        )
        response = self._auth_get(f"/apis/artworks/artworks/{self.artwork.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["images"]), 1)

    def test_artwork_of_inactive_artist_excluded(self):
        Artist.objects.filter(pk=self.artist.pk).update(is_active=False)
        response = self._auth_get("/apis/artworks/artworks/")
        self.assertEqual(response.status_code, 200)
        slugs = [a["slug"] for a in response.json()["results"]]
        self.assertNotIn("obra-1", slugs)

        response = self._auth_get(f"/apis/artworks/artworks/{self.artwork.id}/")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["status"], "error")
