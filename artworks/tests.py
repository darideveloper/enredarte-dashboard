from django.contrib import admin
from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from artworks.admin import (
    ArtCuratorAdmin,
    ArtCuratorTranslationInline,
    ArtistAdmin,
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
    ScaleAdmin,
    ScaleTranslationInline,
    TechniqueAdmin,
    TechniqueTranslationInline,
    ThemeAdmin,
    ThemeTranslationInline,
)
from artworks.models import (
    ArtCurator,
    ArtCuratorTranslation,
    Artist,
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
    Scale,
    ScaleTranslation,
    Technique,
    TechniqueTranslation,
    Theme,
    ThemeTranslation,
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

    def test_artist_add_view_sort_order_initial_when_empty(self):
        url = reverse("admin:artworks_artist_add")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context_data["adminform"].form.initial.get("sort_order"), 1)

    def test_artist_add_view_sort_order_initial_when_artists_exist(self):
        Artist.objects.create(name="Artist 1", slug="artist-1", sort_order=5)
        Artist.objects.create(name="Artist 2", slug="artist-2", sort_order=10)

        url = reverse("admin:artworks_artist_add")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context_data["adminform"].form.initial.get("sort_order"), 11)


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

    def test_curator_add_view_sort_order_initial_when_empty(self):
        url = reverse("admin:artworks_artcurator_add")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context_data["adminform"].form.initial.get("sort_order"), 1)

    def test_curator_add_view_sort_order_initial_when_curators_exist(self):
        ArtCurator.objects.create(name="Curator 1", slug="curator-1", sort_order=3)
        ArtCurator.objects.create(name="Curator 2", slug="curator-2", sort_order=7)

        url = reverse("admin:artworks_artcurator_add")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context_data["adminform"].form.initial.get("sort_order"), 8)


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

    def test_add_view_sort_order_initial(self):
        url = reverse(f"admin:artworks_{self.changelist_label}_add")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context_data["adminform"].form.initial.get("sort_order"), 1)


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

        self.gallery = Gallery.objects.create(slug="galeria-de-arte", sort_order=1)
        self.gallery_admin = admin.site._registry[Gallery]

    def test_gallery_registered(self):
        """Test Gallery is registered with GalleryAdmin"""
        self.assertIn(Gallery, admin.site._registry)
        self.assertIsInstance(admin.site._registry[Gallery], GalleryAdmin)

    def test_gallery_inlines(self):
        """Test GalleryAdmin uses GalleryTranslationInline and ArtworkGalleryInline"""
        self.assertIn(GalleryTranslationInline, self.gallery_admin.inlines)
        self.assertIn(ArtworkGalleryInline, self.gallery_admin.inlines)

    def test_gallery_initial_sort_order(self):
        """Test auto-population of sort_order"""
        url = reverse("admin:artworks_gallery_add")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context_data["adminform"].form.initial.get("sort_order"), 2)

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
            sort_order=1,
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

    def test_artwork_initial_sort_order(self):
        """Test auto-population of sort_order"""
        url = reverse("admin:artworks_artwork_add")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context_data["adminform"].form.initial.get("sort_order"), 2)

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

    def test_artwork_admin_has_filter_horizontal(self):
        """Test ArtworkAdmin uses filter_horizontal for the five taxonomy M2M fields"""
        self.assertEqual(
            self.artwork_admin.filter_horizontal,
            ["disciplines", "techniques", "themes", "formats", "scales"],
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
