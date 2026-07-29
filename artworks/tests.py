from django.contrib import admin
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from artworks.admin import ArtistAdmin, ArtistTranslationInline
from artworks.models import Artist, ArtistTranslation


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

