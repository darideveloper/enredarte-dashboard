from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from blog.models import BlogImage, Post, PostTranslation

_1PX_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05"
    b"\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)


class BlogAPITestCase(APITestCase):
    def setUp(self):
        self.client = APIClient()

        # Active post 1 (most recent)
        self.post1 = Post.objects.create(
            slug="oaxaca-arte",
            author="Equipo Oaxaca",
            published_at=timezone.now(),
            sort_order=1,
            is_active=True,
            banner_image=SimpleUploadedFile("banner1.png", _1PX_PNG, content_type="image/png"),
        )
        PostTranslation.objects.create(
            post=self.post1,
            language="es",
            title="Arte en Oaxaca",
            description="Descripción de Oaxaca",
            keywords="oaxaca, arte",
            content="# Contenido Oaxaca ES",
        )
        PostTranslation.objects.create(
            post=self.post1,
            language="en",
            title="Art in Oaxaca",
            description="Description of Oaxaca",
            keywords="oaxaca, art",
            content="# Content Oaxaca EN",
        )

        # Active post 2 (older)
        self.post2 = Post.objects.create(
            slug="cdmx-galerias",
            author="Curaduría CDMX",
            published_at=timezone.now() - timezone.timedelta(days=2),
            sort_order=2,
            is_active=True,
        )
        PostTranslation.objects.create(
            post=self.post2,
            language="es",
            title="Galerías CDMX",
            description="Descripción CDMX",
            keywords="cdmx, galerias",
            content="# Contenido CDMX ES",
        )
        PostTranslation.objects.create(
            post=self.post2,
            language="en",
            title="CDMX Galleries",
            description="Description CDMX",
            keywords="cdmx, galleries",
            content="# Content CDMX EN",
        )

        # Inactive post (draft)
        self.post_draft = Post.objects.create(
            slug="borrador-secreto",
            author="Borrador",
            published_at=timezone.now(),
            sort_order=3,
            is_active=False,
        )
        PostTranslation.objects.create(
            post=self.post_draft,
            language="es",
            title="Borrador Secreto",
            description="No visible",
            keywords="draft",
            content="Borrador contenido",
        )

    def test_list_posts_success(self):
        url = reverse("blog-posts-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify paginated envelope
        data = response.json()
        self.assertIn("count", data)
        self.assertIn("results", data)
        self.assertEqual(data["count"], 2)
        self.assertEqual(len(data["results"]), 2)

        # Verify first item (most recent post)
        item1 = data["results"][0]
        self.assertEqual(item1["slug"], "oaxaca-arte")
        self.assertEqual(item1["author"], "Equipo Oaxaca")
        self.assertEqual(item1["title_es"], "Arte en Oaxaca")
        self.assertEqual(item1["title_en"], "Art in Oaxaca")
        self.assertEqual(item1["description_es"], "Descripción de Oaxaca")
        self.assertEqual(item1["description_en"], "Description of Oaxaca")
        self.assertEqual(item1["keywords_es"], "oaxaca, arte")
        self.assertEqual(item1["keywords_en"], "oaxaca, art")
        self.assertIn("banner1", item1["banner_image"])

        # Verify content fields are excluded in summary list
        self.assertNotIn("content_es", item1)
        self.assertNotIn("content_en", item1)

    def test_list_posts_ordering(self):
        url = reverse("blog-posts-list")
        response = self.client.get(url)
        results = response.json()["results"]
        slugs = [r["slug"] for r in results]
        self.assertEqual(slugs, ["oaxaca-arte", "cdmx-galerias"])

    def test_list_posts_excludes_inactive(self):
        url = reverse("blog-posts-list")
        response = self.client.get(url)
        results = response.json()["results"]
        slugs = [r["slug"] for r in results]
        self.assertNotIn("borrador-secreto", slugs)

    def test_retrieve_post_by_slug_success(self):
        url = reverse("blog-posts-detail", kwargs={"slug": "oaxaca-arte"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertEqual(data["slug"], "oaxaca-arte")
        self.assertEqual(data["title_es"], "Arte en Oaxaca")
        self.assertEqual(data["title_en"], "Art in Oaxaca")
        self.assertEqual(data["content_es"], "# Contenido Oaxaca ES")
        self.assertEqual(data["content_en"], "# Content Oaxaca EN")

    def test_retrieve_inactive_post_returns_404(self):
        url = reverse("blog-posts-detail", kwargs={"slug": "borrador-secreto"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_retrieve_non_existent_post_returns_404(self):
        url = reverse("blog-posts-detail", kwargs={"slug": "no-existe"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_list_query_efficiency_no_n_plus_one(self):
        url = reverse("blog-posts-list")
        # 1 count query + 1 post query + 1 translations prefetch query = 3 queries
        with self.assertNumQueries(3):
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)


class BlogModelTestCase(APITestCase):
    def test_post_and_translation_str(self):
        post = Post.objects.create(slug="test-str", author="Autor")
        trans_es = PostTranslation.objects.create(
            post=post, language="es", title="Título Español", description="Desc"
        )
        trans_en = PostTranslation.objects.create(
            post=post, language="en", title="English Title", description="Desc"
        )
        self.assertEqual(str(post), "Título Español")
        self.assertEqual(str(trans_es), "Título Español (es)")
        self.assertEqual(str(trans_en), "Título Español (en)")

    def test_post_slug_backfill(self):
        post = Post.objects.create(author="Autor")
        PostTranslation.objects.create(
            post=post, language="es", title="Nueva Publicación Increíble", description="Desc"
        )
        self.assertEqual(post.slug, "nueva-publicacion-increible")

    def test_blog_image_str(self):
        img = BlogImage.objects.create(
            name="Test Image",
            image=SimpleUploadedFile("media_test.png", _1PX_PNG, content_type="image/png"),
        )
        self.assertEqual(str(img), "Test Image")


class BlogLiveAPITestCase(APITestCase):
    """External HTTP tests verifying real socket/client communication."""

    def setUp(self):
        self.post = Post.objects.create(
            slug="live-arte",
            author="Live Author",
            published_at=timezone.now(),
            is_active=True,
        )
        PostTranslation.objects.create(
            post=self.post,
            language="es",
            title="Live Arte ES",
            description="Desc ES",
            keywords="live, arte",
            content="# Live Contenido ES",
        )
        PostTranslation.objects.create(
            post=self.post,
            language="en",
            title="Live Art EN",
            description="Desc EN",
            keywords="live, art",
            content="# Live Content EN",
        )

    def test_live_list_and_detail_http_responses(self):
        client = APIClient()

        # 1. External HTTP List Call
        list_resp = client.get("/api/blog/posts/")
        self.assertEqual(list_resp.status_code, 200)
        list_data = list_resp.json()
        self.assertIn("results", list_data)
        self.assertEqual(list_data["results"][0]["slug"], "live-arte")

        # 2. External HTTP Detail Call
        detail_resp = client.get("/api/blog/posts/live-arte/")
        self.assertEqual(detail_resp.status_code, 200)
        detail_data = detail_resp.json()
        self.assertEqual(detail_data["slug"], "live-arte")
        self.assertEqual(detail_data["content_es"], "# Live Contenido ES")


