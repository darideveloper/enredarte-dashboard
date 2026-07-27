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
