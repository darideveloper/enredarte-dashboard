from unittest.mock import MagicMock, patch

from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase, override_settings
from django.urls import reverse


def make_urlopen_mock(status=200):
    response = MagicMock()
    response.status = status
    context = MagicMock()
    context.__enter__.return_value = response
    return MagicMock(return_value=context)


class PublishChangesViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.staff = User.objects.create_user(username="staff", password="pw", is_staff=True)
        cls.plain = User.objects.create_user(username="plain", password="pw", is_staff=False)
        cls.url = reverse("core:publish-changes")

    @override_settings(DEPLOY_WEBHOOK_URL="", COOLIFY_API_TOKEN="")
    def test_staff_gets_redirect_and_success_message(self):
        self.client.force_login(self.staff)
        response = self.client.get(self.url)
        self.assertRedirects(response, reverse("admin:index"))
        texts = [m.message for m in get_messages(response.wsgi_request)]
        self.assertIn(
            "Cambios publicados correctamente, espere 5-10 minutos para verlos "
            "reflejados en la web (preferiblemente use una ventana de incógnito)",
            texts,
        )

    def test_non_staff_cannot_trigger(self):
        self.client.force_login(self.plain)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login/", response["Location"])

    def test_anonymous_redirects_to_login(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login/", response["Location"])

    def test_failure_surfaces_error_message(self):
        self.client.force_login(self.staff)
        with patch("core.views.publish_changes", side_effect=RuntimeError("boom")):
            response = self.client.get(self.url)
        self.assertRedirects(response, reverse("admin:index"))
        texts = [m.message for m in get_messages(response.wsgi_request)]
        self.assertTrue(any("boom" in t for t in texts))

    @override_settings(
        DEPLOY_WEBHOOK_URL="https://example.test/deploy?uuid=x&force=false",
        COOLIFY_API_TOKEN="secret-token",
    )
    def test_configured_webhook_requests_without_logging_secrets(self):
        from core.services import publishing

        urlopen_mock = make_urlopen_mock(status=200)
        with (
            patch.object(publishing.urllib.request, "urlopen", urlopen_mock),
            self.assertLogs("core.services.publishing", level="INFO") as logs,
        ):
            self.assertTrue(publishing.publish_changes())
        called_request = urlopen_mock.call_args[0][0]
        self.assertEqual(
            called_request.full_url, "https://example.test/deploy?uuid=x&force=false"
        )
        self.assertEqual(called_request.get_method(), "GET")
        self.assertEqual(
            called_request.get_header("Authorization"), "Bearer secret-token"
        )
        self.assertEqual(
            called_request.get_header("User-agent"), "enredarte-dashboard/1.0"
        )
        for line in logs.output:
            self.assertNotIn("example.test", line)
            self.assertNotIn("uuid", line)
            self.assertNotIn("secret-token", line)

    @override_settings(
        DEPLOY_WEBHOOK_URL="https://example.test/deploy?uuid=x&force=false",
        COOLIFY_API_TOKEN="",
    )
    def test_missing_token_fails_clearly_without_request(self):
        from core.services import publishing

        with patch.object(
            publishing.urllib.request, "urlopen", make_urlopen_mock()
        ) as urlopen_mock:
            with self.assertRaisesMessage(
                RuntimeError, "COOLIFY_API_TOKEN sin configurar"
            ):
                publishing.publish_changes()
        urlopen_mock.assert_not_called()

    @override_settings(
        DEPLOY_WEBHOOK_URL="https://example.test/deploy?uuid=x&force=false",
        COOLIFY_API_TOKEN="bad-token",
    )
    def test_forbidden_hints_at_token_permission(self):
        import urllib.error

        from core.services import publishing

        def raise_403(request, timeout=None):
            raise urllib.error.HTTPError(
                request.full_url, 403, "Forbidden", {}, None
            )

        with patch.object(
            publishing.urllib.request, "urlopen", side_effect=raise_403
        ):
            with self.assertRaisesMessage(RuntimeError, "permiso deploy"):
                publishing.publish_changes()

    @override_settings(
        DEPLOY_WEBHOOK_URL="https://example.test/deploy?uuid=x&force=false",
        COOLIFY_API_TOKEN="tok",
    )
    def test_cloudflare_block_hints_at_waf(self):
        import io
        import urllib.error

        from core.services import publishing

        def raise_cf_block(request, timeout=None):
            raise urllib.error.HTTPError(
                request.full_url,
                403,
                "Forbidden",
                {},
                io.BytesIO(b"error code: 1010"),
            )

        with patch.object(
            publishing.urllib.request, "urlopen", side_effect=raise_cf_block
        ):
            with self.assertRaisesMessage(RuntimeError, "Cloudflare"):
                publishing.publish_changes()

    def test_staff_sees_sidebar_button(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse("admin:index"))
        self.assertContains(response, "Publicar Cambios")

    def test_non_staff_sidebar_hides_button(self):
        self.client.force_login(self.plain)
        response = self.client.get(reverse("admin:index"), follow=True)
        self.assertNotContains(response, "Publicar Cambios")


class StripeInitTest(TestCase):
    """W3: `core.stripe` initializes the SDK and fails fast outside dev."""

    def tearDown(self):
        import importlib

        import core.stripe

        # Reload with the real settings so patched api_key/version never leak.
        importlib.reload(core.stripe)

    @override_settings(
        STRIPE_SECRET_KEY="sk_test_init",
        STRIPE_API_VERSION="2024-06-20",
        STRIPE_WEBHOOK_SECRET="whsec_x",
    )
    @patch.dict("os.environ", {"ENV": "dev"})
    def test_dev_sets_api_key_and_version(self):
        import importlib

        import stripe

        import core.stripe

        importlib.reload(core.stripe)
        self.assertEqual(stripe.api_key, "sk_test_init")
        self.assertEqual(stripe.api_version, "2024-06-20")

    @override_settings(STRIPE_SECRET_KEY="", STRIPE_WEBHOOK_SECRET="whsec_x")
    @patch.dict("os.environ", {"ENV": "prod"})
    def test_missing_secret_key_refuses_outside_dev(self):
        import importlib

        import core.stripe

        with self.assertRaises(ImproperlyConfigured):
            importlib.reload(core.stripe)

    @override_settings(STRIPE_SECRET_KEY="sk_test_init", STRIPE_WEBHOOK_SECRET="not-a-secret")
    @patch.dict("os.environ", {"ENV": "prod"})
    def test_missing_webhook_secret_refuses_outside_dev(self):
        import importlib

        import core.stripe

        with self.assertRaises(ImproperlyConfigured):
            importlib.reload(core.stripe)


class StripeEventAdminTest(TestCase):
    """W5: the audit page survives the model move and stays read-only/ordered."""

    @classmethod
    def setUpTestData(cls):
        cls.admin_user = User.objects.create_superuser(
            username="stripe_admin", password="pw", email="admin@x.com"
        )

    def setUp(self):
        self.client.force_login(self.admin_user)

    def _make(self, event_id, event_type, payload, error=""):
        from core.models import StripeEvent

        return StripeEvent.objects.create(
            event_id=event_id, event_type=event_type, payload=payload, error=error
        )

    def test_registered_from_core_admin_and_readonly(self):
        from django.contrib import admin as dj_admin

        from core.models import StripeEvent

        model_admin = dj_admin.site._registry[StripeEvent]
        self.assertEqual(model_admin.__class__.__module__, "core.admin")
        self.assertFalse(model_admin.has_add_permission(None))
        self.assertFalse(model_admin.has_change_permission(None))
        self.assertFalse(model_admin.has_delete_permission(None))
        self.assertEqual(list(StripeEvent._meta.ordering), ["-received_at"])

    def test_changelist_lists_events(self):
        self._make("evt_admin_1", "invoice.paid", {"a": 1})
        response = self.client.get(reverse("admin:core_stripeevent_changelist"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "invoice.paid")

    def test_change_view_shows_error_and_payload(self):
        event = self._make("evt_admin_2", "invoice.failed", {"b": 2}, error="boom")
        response = self.client.get(
            reverse("admin:core_stripeevent_change", args=[event.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "boom")
