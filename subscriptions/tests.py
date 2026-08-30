import hashlib
import hmac
import json
import time
from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from artworks.models import Artist
from subscriptions.models import ArtistSubscription, BillingPlan, StripeEvent
from subscriptions.services.subscription_state import compute_is_active

User = get_user_model()
WEBHOOK_SECRET = "whsec_test"


def stripe_signature(payload, secret=WEBHOOK_SECRET, timestamp=None):
    """Build a valid Stripe-Signature header for `payload` (bytes)."""
    timestamp = timestamp or int(time.time())
    signed = f"{timestamp}.{payload.decode()}".encode()
    sig = hmac.new(secret.encode(), signed, hashlib.sha256).hexdigest()
    return f"t={timestamp},v1={sig}"


def make_subscription(status="active", cancel_at_period_end=False, period_end=None):
    """Minimal Stripe subscription dict."""
    return {
        "id": "sub_123",
        "customer": "cus_123",
        "customer_email": "a@x.com",
        "status": status,
        "cancel_at_period_end": cancel_at_period_end,
        "current_period_end": period_end,
    }


def make_event(event_type, event_id, obj):
    return {"id": event_id, "type": event_type, "data": {"object": obj}}


def future_epoch(days=10):
    return int(time.time()) + days * 86400


def past_epoch(days=10):
    return int(time.time()) - days * 86400


def make_invoice(customer_id, subscription_id, period_end=None, invoice_id="in_1"):
    """Minimal Stripe invoice dict."""
    return {
        "id": invoice_id,
        "customer": customer_id,
        "subscription": subscription_id,
        "lines": {"data": [{"period": {"end": period_end}}]},
    }


class ArtistTestBase(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser("admin", "admin@x.com", "x")
        self.artist = self.make_artist("Artista Uno", "artista@x.com")

    def make_artist(self, name, email="a@x.com", slug=None):
        return Artist.objects.create(
            name=name,
            email=email,
            slug=slug or f"{name.lower().replace(' ', '-')}-{self._testMethodName}",
        )

    def _action_url(self, artist, action):
        return f"/admin/artworks/artist/{artist.pk}/change/{action}/"


class ComputeIsActiveTest(ArtistTestBase):
    def test_no_subscription_returns_artist_default(self):
        self.assertEqual(compute_is_active(None, artist=self.artist), self.artist.is_active)

    def test_active_is_visible(self):
        artist = self.make_artist("Artista activo")
        sub = ArtistSubscription.objects.create(
            artist=artist, status=ArtistSubscription.Status.ACTIVE
        )
        self.assertTrue(compute_is_active(sub))

    def test_pending_is_not_visible(self):
        artist = self.make_artist("Artista pendiente")
        sub = ArtistSubscription.objects.create(
            artist=artist, status=ArtistSubscription.Status.PENDING
        )
        self.assertFalse(compute_is_active(sub))

    def test_canceling_future_period_is_visible(self):
        sub = ArtistSubscription.objects.create(
            artist=self.artist,
            status=ArtistSubscription.Status.CANCELING,
            current_period_end=timezone.now() + timedelta(days=5),
        )
        self.assertTrue(compute_is_active(sub))

    def test_canceling_past_period_is_invisible(self):
        sub = ArtistSubscription.objects.create(
            artist=self.artist,
            status=ArtistSubscription.Status.CANCELING,
            current_period_end=timezone.now() - timedelta(days=1),
        )
        self.assertFalse(compute_is_active(sub))

    def test_past_due_within_grace_is_visible(self):
        BillingPlan.get_solo().save()
        sub = ArtistSubscription.objects.create(
            artist=self.artist,
            status=ArtistSubscription.Status.PAST_DUE,
            current_period_end=timezone.now() + timedelta(days=1),
        )
        self.assertTrue(compute_is_active(sub))

    def test_past_due_past_grace_is_invisible(self):
        BillingPlan.get_solo().save()
        sub = ArtistSubscription.objects.create(
            artist=self.artist,
            status=ArtistSubscription.Status.PAST_DUE,
            current_period_end=timezone.now() - timedelta(days=10),
        )
        self.assertFalse(compute_is_active(sub))

    def test_canceled_is_invisible(self):
        sub = ArtistSubscription.objects.create(
            artist=self.artist, status=ArtistSubscription.Status.CANCELED
        )
        self.assertFalse(compute_is_active(sub))


@override_settings(STRIPE_WEBHOOK_SECRET=WEBHOOK_SECRET)
class WebhookTest(ArtistTestBase):
    def post(self, payload):
        return self.client.post(
            "/webhooks/stripe/",
            data=payload,
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE=stripe_signature(payload),
        )

    def test_get_is_rejected(self):
        response = self.client.get("/webhooks/stripe/")
        self.assertEqual(response.status_code, 405)

    def test_missing_signature_is_400(self):
        response = self.client.post(
            "/webhooks/stripe/", data=b"{}", content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)

    def test_invalid_signature_is_400(self):
        response = self.client.post(
            "/webhooks/stripe/",
            data=b"{}",
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="t=1,v1=deadbeef",
        )
        self.assertEqual(response.status_code, 400)

    def test_unhandled_event_is_recorded_and_ok(self):
        event = make_event("unknown.type", "evt_unknown", {"id": "obj_1"})
        payload = json.dumps(event).encode()
        response = self.post(payload)
        self.assertEqual(response.status_code, 200)
        record = StripeEvent.objects.get(event_id="evt_unknown")
        self.assertEqual(record.error, "")
        self.assertIsNotNone(record.processed_at)

    def test_subscription_created_activates_artist(self):
        sub = ArtistSubscription.objects.create(
            artist=self.artist,
            stripe_customer_id="cus_123",
            signup_url="https://checkout.stripe.com/x",
        )
        event = make_event(
            "customer.subscription.created", "evt_created", make_subscription()
        )
        payload = json.dumps(event).encode()
        response = self.post(payload)
        self.assertEqual(response.status_code, 200)
        sub.refresh_from_db()
        self.assertEqual(sub.status, ArtistSubscription.Status.ACTIVE)
        self.assertEqual(sub.stripe_subscription_id, "sub_123")
        self.assertEqual(sub.signup_url, "")
        self.artist.refresh_from_db()
        self.assertTrue(self.artist.is_active)

    def test_duplicate_event_is_noop(self):
        sub = ArtistSubscription.objects.create(
            artist=self.artist, stripe_customer_id="cus_123"
        )
        event = make_event(
            "customer.subscription.created", "evt_dup", make_subscription()
        )
        payload = json.dumps(event).encode()
        self.assertEqual(self.post(payload).status_code, 200)
        sub.refresh_from_db()
        self.assertEqual(sub.status, ArtistSubscription.Status.ACTIVE)
        self.assertEqual(StripeEvent.objects.count(), 1)
        self.assertEqual(self.post(payload).status_code, 200)
        sub.refresh_from_db()
        self.assertEqual(sub.status, ArtistSubscription.Status.ACTIVE)
        self.assertEqual(StripeEvent.objects.count(), 1)

    def test_handler_crash_records_error_and_returns_500(self):
        event = make_event(
            "customer.subscription.created", "evt_crash", make_subscription()
        )
        payload = json.dumps(event).encode()

        def raiser(event_dict):
            raise RuntimeError("boom")

        self.client.raise_request_exception = False
        with patch.dict(
            "subscriptions.webhooks.HANDLERS",
            {"customer.subscription.created": raiser},
        ):
            response = self.post(payload)
        self.assertEqual(response.status_code, 500)
        record = StripeEvent.objects.get(event_id="evt_crash")
        self.assertIn("boom", record.error)
        self.assertIsNone(record.processed_at)

    def test_checkout_completed_correlates_via_metadata(self):
        sub = ArtistSubscription.objects.create(artist=self.artist)
        session = {
            "id": "cs_1",
            "metadata": {"artist_id": str(self.artist.pk)},
            "customer": "cus_abc",
            "subscription": "sub_abc",
        }
        event = make_event("checkout.session.completed", "evt_checkout", session)
        payload = json.dumps(event).encode()
        response = self.post(payload)
        self.assertEqual(response.status_code, 200)
        sub.refresh_from_db()
        self.assertEqual(sub.stripe_customer_id, "cus_abc")
        self.assertEqual(sub.stripe_subscription_id, "sub_abc")
        self.assertEqual(sub.status, ArtistSubscription.Status.PENDING)
        self.artist.refresh_from_db()
        self.assertFalse(self.artist.is_active)

    def test_checkout_completed_unknown_artist_is_noop(self):
        session = {
            "id": "cs_2",
            "metadata": {"artist_id": "99999"},
            "customer": "cus_abc",
            "subscription": "sub_abc",
        }
        event = make_event("checkout.session.completed", "evt_checkout_unk", session)
        payload = json.dumps(event).encode()
        response = self.post(payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ArtistSubscription.objects.count(), 0)

    def test_subscription_updated_canceling_keeps_artist_visible(self):
        sub = ArtistSubscription.objects.create(
            artist=self.artist,
            status=ArtistSubscription.Status.ACTIVE,
            stripe_customer_id="cus_123",
            stripe_subscription_id="sub_123",
            current_period_end=timezone.now() + timedelta(days=5),
        )
        event = make_event(
            "customer.subscription.updated",
            "evt_canceling",
            make_subscription(
                status="active", cancel_at_period_end=True, period_end=future_epoch()
            ),
        )
        payload = json.dumps(event).encode()
        response = self.post(payload)
        self.assertEqual(response.status_code, 200)
        sub.refresh_from_db()
        self.assertEqual(sub.status, ArtistSubscription.Status.CANCELING)
        self.assertTrue(sub.cancel_at_period_end)
        self.artist.refresh_from_db()
        self.assertTrue(self.artist.is_active)

    def test_subscription_deleted_flips_artist_inactive(self):
        sub = ArtistSubscription.objects.create(
            artist=self.artist,
            status=ArtistSubscription.Status.ACTIVE,
            stripe_customer_id="cus_123",
            stripe_subscription_id="sub_123",
        )
        event = make_event(
            "customer.subscription.deleted",
            "evt_deleted",
            make_subscription(status="canceled"),
        )
        payload = json.dumps(event).encode()
        response = self.post(payload)
        self.assertEqual(response.status_code, 200)
        sub.refresh_from_db()
        self.assertEqual(sub.status, ArtistSubscription.Status.CANCELED)
        self.artist.refresh_from_db()
        self.assertFalse(self.artist.is_active)

    def test_invoice_payment_succeeded_resumes_lapsed_artist(self):
        sub = ArtistSubscription.objects.create(
            artist=self.artist,
            status=ArtistSubscription.Status.CANCELED,
            stripe_customer_id="cus_123",
            stripe_subscription_id="sub_123",
        )
        self.artist.is_active = False
        self.artist.save(update_fields=["is_active"])
        event = make_event(
            "invoice.payment_succeeded",
            "evt_inv_ok",
            make_invoice("cus_123", "sub_123", period_end=future_epoch()),
        )
        payload = json.dumps(event).encode()
        response = self.post(payload)
        self.assertEqual(response.status_code, 200)
        sub.refresh_from_db()
        self.assertEqual(sub.status, ArtistSubscription.Status.ACTIVE)
        self.assertIsNotNone(sub.current_period_end)
        self.artist.refresh_from_db()
        self.assertTrue(self.artist.is_active)

    def test_invoice_payment_failed_sets_past_due(self):
        sub = ArtistSubscription.objects.create(
            artist=self.artist,
            status=ArtistSubscription.Status.ACTIVE,
            stripe_customer_id="cus_123",
            stripe_subscription_id="sub_123",
        )
        event = make_event(
            "invoice.payment_failed",
            "evt_inv_fail",
            make_invoice("cus_123", "sub_123", period_end=future_epoch()),
        )
        payload = json.dumps(event).encode()
        response = self.post(payload)
        self.assertEqual(response.status_code, 200)
        sub.refresh_from_db()
        self.assertEqual(sub.status, ArtistSubscription.Status.PAST_DUE)
        self.artist.refresh_from_db()
        self.assertTrue(self.artist.is_active)


class AdminEndpointTest(ArtistTestBase):
    def test_non_staff_is_redirected_to_admin_login(self):
        user = User.objects.create_user("viewer", "v@x.com", "x")
        self.client.force_login(user)
        response = self.client.get(self._action_url(self.artist, "generate-link"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login/", response.url)

    def test_generate_link_creates_pending_subscription(self):
        self.client.force_login(self.user)
        BillingPlan.get_solo().save()
        BillingPlan.objects.update(stripe_price_id="price_test")
        session = type("S", (), {"url": "https://checkout.stripe.com/c/pay", "expires_at": time.time() + 3600})
        with patch(
            "artworks.admin.stripe_client.create_customer",
            return_value=type("C", (), {"id": "cus_new"}),
        ), patch(
            "artworks.admin.stripe_client.create_checkout_session",
            return_value=session,
        ):
            response = self.client.get(self._action_url(self.artist, "generate-link"))
        self.assertEqual(response.status_code, 302)
        sub = ArtistSubscription.objects.get(artist=self.artist)
        self.assertEqual(sub.status, ArtistSubscription.Status.PENDING)
        self.assertEqual(sub.stripe_customer_id, "cus_new")
        self.assertEqual(sub.signup_url, "https://checkout.stripe.com/c/pay")
        self.artist.refresh_from_db()
        self.assertFalse(self.artist.is_active)

    def test_generate_link_without_email_errors(self):
        self.client.force_login(self.user)
        artist = self.make_artist("Sin correo", email="")
        with patch(
            "artworks.admin.stripe_client.create_customer"
        ) as create_customer:
            response = self.client.get(self._action_url(artist, "generate-link"))
        self.assertEqual(response.status_code, 302)
        create_customer.assert_not_called()
        self.assertFalse(ArtistSubscription.objects.filter(artist=artist).exists())

    def test_generate_link_blocked_by_inactive_billing_plan(self):
        self.client.force_login(self.user)
        BillingPlan.get_solo().save()
        BillingPlan.objects.update(is_active_for_new_signups=False)
        with patch(
            "artworks.admin.stripe_client.create_customer"
        ) as create_customer:
            response = self.client.get(self._action_url(self.artist, "generate-link"))
        self.assertEqual(response.status_code, 302)
        create_customer.assert_not_called()
        self.assertFalse(ArtistSubscription.objects.filter(artist=self.artist).exists())

    def test_generate_link_blocked_by_missing_price_id(self):
        self.client.force_login(self.user)
        BillingPlan.get_solo().save()
        BillingPlan.objects.update(stripe_price_id="")
        with patch(
            "artworks.admin.stripe_client.create_customer"
        ) as create_customer:
            response = self.client.get(self._action_url(self.artist, "generate-link"))
        self.assertEqual(response.status_code, 302)
        create_customer.assert_not_called()
        self.assertFalse(ArtistSubscription.objects.filter(artist=self.artist).exists())

    def test_regenerate_link_reuses_valid_url(self):
        self.client.force_login(self.user)
        BillingPlan.get_solo().save()
        BillingPlan.objects.update(stripe_price_id="price_test")
        sub = ArtistSubscription.objects.create(
            artist=self.artist,
            stripe_customer_id="cus_123",
            signup_url="https://checkout.stripe.com/c/valid",
            signup_url_expires_at=timezone.now() + timedelta(hours=1),
        )
        with patch(
            "artworks.admin.stripe_client.create_checkout_session"
        ) as create_session:
            response = self.client.get(self._action_url(self.artist, "regenerate-link"))
        self.assertEqual(response.status_code, 302)
        create_session.assert_not_called()
        sub.refresh_from_db()
        self.assertEqual(sub.signup_url, "https://checkout.stripe.com/c/valid")

    def test_regenerate_link_creates_fresh_session_when_expired(self):
        self.client.force_login(self.user)
        BillingPlan.get_solo().save()
        BillingPlan.objects.update(stripe_price_id="price_test")
        sub = ArtistSubscription.objects.create(
            artist=self.artist,
            status=ArtistSubscription.Status.PENDING,
            stripe_customer_id="cus_123",
            signup_url="https://checkout.stripe.com/c/old",
            signup_url_expires_at=timezone.now() - timedelta(hours=1),
        )
        session = type("S", (), {"url": "https://checkout.stripe.com/c/new", "expires_at": future_epoch()})
        with patch(
            "artworks.admin.stripe_client.create_checkout_session",
            return_value=session,
        ) as create_session:
            response = self.client.get(self._action_url(self.artist, "regenerate-link"))
        self.assertEqual(response.status_code, 302)
        create_session.assert_called_once()
        sub.refresh_from_db()
        self.assertEqual(sub.signup_url, "https://checkout.stripe.com/c/new")
        self.assertEqual(sub.stripe_customer_id, "cus_123")
        self.assertEqual(sub.status, ArtistSubscription.Status.PENDING)

    def test_open_portal_without_customer_warns_and_skips_api(self):
        self.client.force_login(self.user)
        ArtistSubscription.objects.create(
            artist=self.artist, signup_url="https://checkout.stripe.com/c/x"
        )
        with patch(
            "artworks.admin.stripe_client.create_billing_portal_session"
        ) as create_portal:
            response = self.client.get(self._action_url(self.artist, "open-portal"))
        self.assertEqual(response.status_code, 302)
        create_portal.assert_not_called()

    def test_open_portal_returns_portal_url_in_message(self):
        self.client.force_login(self.user)
        ArtistSubscription.objects.create(
            artist=self.artist,
            stripe_customer_id="cus_123",
            signup_url="https://checkout.stripe.com/c/x",
        )
        portal = type("P", (), {"url": "https://billing.stripe.com/p/session"})
        with patch(
            "artworks.admin.stripe_client.create_billing_portal_session",
            return_value=portal,
        ):
            response = self.client.get(
                self._action_url(self.artist, "open-portal"), follow=True
            )
        self.assertContains(response, "https://billing.stripe.com/p/session")

    def test_sync_from_stripe_without_customer_warns(self):
        self.client.force_login(self.user)
        ArtistSubscription.objects.create(artist=self.artist)
        with patch(
            "artworks.admin.stripe_client.fetch_customer"
        ) as fetch_customer:
            response = self.client.get(self._action_url(self.artist, "sync-from-stripe"))
        self.assertEqual(response.status_code, 302)
        fetch_customer.assert_not_called()

    def test_sync_from_stripe_reconciles_state(self):
        self.client.force_login(self.user)
        sub = ArtistSubscription.objects.create(
            artist=self.artist,
            status=ArtistSubscription.Status.PENDING,
            stripe_customer_id="cus_123",
        )
        self.artist.is_active = False
        self.artist.save(update_fields=["is_active"])
        with patch(
            "artworks.admin.stripe_client.fetch_customer",
            return_value=type("C", (), {"email": "a@x.com"}),
        ), patch(
            "artworks.admin.stripe_client.list_subscriptions",
            return_value=[make_subscription(status="active", period_end=future_epoch())],
        ):
            response = self.client.get(self._action_url(self.artist, "sync-from-stripe"))
        self.assertEqual(response.status_code, 302)
        sub.refresh_from_db()
        self.assertEqual(sub.status, ArtistSubscription.Status.ACTIVE)
        self.assertEqual(sub.customer_email, "a@x.com")
        self.assertIsNotNone(sub.last_synced_at)
        self.artist.refresh_from_db()
        self.assertTrue(self.artist.is_active)

    def test_sync_from_stripe_no_subscriptions_sets_canceled(self):
        self.client.force_login(self.user)
        sub = ArtistSubscription.objects.create(
            artist=self.artist,
            status=ArtistSubscription.Status.PENDING,
            stripe_customer_id="cus_123",
        )
        with patch(
            "artworks.admin.stripe_client.fetch_customer",
            return_value=type("C", (), {"email": "a@x.com"}),
        ), patch(
            "artworks.admin.stripe_client.list_subscriptions",
            return_value=[],
        ):
            response = self.client.get(self._action_url(self.artist, "sync-from-stripe"))
        self.assertEqual(response.status_code, 302)
        sub.refresh_from_db()
        self.assertEqual(sub.status, ArtistSubscription.Status.CANCELED)
        self.artist.refresh_from_db()
        self.assertFalse(self.artist.is_active)

    def test_landing_pages_render(self):
        response = self.client.get(reverse("subscriptions:success"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "¡Gracias! Tu suscripción está activa.")
        response = self.client.get(reverse("subscriptions:cancel"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tu pago fue cancelado.")
        response = self.client.get(reverse("subscriptions:portal-return"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Gracias por usar el portal de gestión.")


class ArtistAdminBadgeTest(ArtistTestBase):
    def test_changelist_shows_no_subscription(self):
        self.client.force_login(self.user)
        response = self.client.get("/admin/artworks/artist/")
        self.assertContains(response, "Sin suscripción")

    def test_changelist_shows_active_badge(self):
        ArtistSubscription.objects.create(
            artist=self.artist, status=ArtistSubscription.Status.ACTIVE
        )
        self.client.force_login(self.user)
        response = self.client.get("/admin/artworks/artist/")
        self.assertContains(response, "Activa")

    def test_change_view_has_action_buttons(self):
        self.client.force_login(self.user)
        response = self.client.get(
            f"/admin/artworks/artist/{self.artist.pk}/change/"
        )
        self.assertContains(response, "Generar link de suscripción")
        self.assertContains(response, "Sincronizar desde Stripe")
        self.assertNotContains(response, "Copiar link")
        self.assertNotContains(response, "Regenerar link")
        self.assertNotContains(response, "Abrir Customer Portal")

    def test_change_view_shows_copy_button_when_link_exists(self):
        ArtistSubscription.objects.create(
            artist=self.artist,
            signup_url="https://checkout.stripe.com/c/pay",
            signup_url_expires_at=timezone.now() + timedelta(hours=1),
        )
        self.client.force_login(self.user)
        response = self.client.get(
            f"/admin/artworks/artist/{self.artist.pk}/change/"
        )
        self.assertContains(response, "Copiar link")
        self.assertContains(
            response, "data-copy-url=\"https://checkout.stripe.com/c/pay\""
        )
        self.assertContains(response, "Regenerar link")
        self.assertContains(response, "Abrir Customer Portal")
        self.assertContains(response, "Sincronizar desde Stripe")
        self.assertNotContains(response, "Generar link de suscripción")

    def test_change_view_hides_copy_button_when_link_expired(self):
        ArtistSubscription.objects.create(
            artist=self.artist,
            signup_url="https://checkout.stripe.com/c/old",
            signup_url_expires_at=timezone.now() - timedelta(hours=1),
        )
        self.client.force_login(self.user)
        response = self.client.get(
            f"/admin/artworks/artist/{self.artist.pk}/change/"
        )
        self.assertNotContains(response, "Copiar link")
        self.assertNotContains(response, "Generar link de suscripción")
        self.assertContains(response, "Regenerar link")
        self.assertContains(response, "Abrir Customer Portal")
        self.assertContains(response, "Sincronizar desde Stripe")

    def test_changelist_shows_canceling_badge(self):
        ArtistSubscription.objects.create(
            artist=self.artist, status=ArtistSubscription.Status.CANCELING
        )
        self.client.force_login(self.user)
        response = self.client.get("/admin/artworks/artist/")
        self.assertContains(response, "Cancelada, vigente hasta fin de período")

    def test_changelist_shows_past_due_badge(self):
        ArtistSubscription.objects.create(
            artist=self.artist, status=ArtistSubscription.Status.PAST_DUE
        )
        self.client.force_login(self.user)
        response = self.client.get("/admin/artworks/artist/")
        self.assertContains(response, "Pago fallido (en gracia)")

    def test_changelist_shows_canceled_badge(self):
        ArtistSubscription.objects.create(
            artist=self.artist, status=ArtistSubscription.Status.CANCELED
        )
        self.client.force_login(self.user)
        response = self.client.get("/admin/artworks/artist/")
        self.assertContains(response, "Cancelada definitivamente")
