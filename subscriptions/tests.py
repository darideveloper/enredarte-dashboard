import hashlib
import hmac
import json
import time
from datetime import timedelta
from unittest.mock import patch

from decimal import Decimal

import stripe as stripe_lib
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from artworks.models import Artist
from subscriptions.admin import BillingPlanForm
from subscriptions.models import ArtistSubscription, BillingPlan, BillingPlanPriceHistory, StripeEvent
from subscriptions.services.subscription_state import compute_is_active
from subscriptions.webhooks import _handle_subscription_created

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


def _make_list_object(data):
    """Return a minimal Stripe ListObject-shaped mock.

    Replicates the real SDK guard at ``stripe/_list_object.py:99``: integer
    indexing raises ``KeyError`` so ``subs[0]`` crashes while ``subs.data[0]``
    succeeds. Existing tests keep plain-list mocks (backward-compatible via
    ``hasattr(subs, \"data\")`` guard in ``artworks/admin.py:sync_from_stripe``);
    these ListObject cases prove the fix handles the real SDK shape.
    """

    class _ListObject:
        def __init__(self, data):
            self.data = data

        def __getitem__(self, key):
            if isinstance(key, str):
                return getattr(self, key)
            raise KeyError(
                "You tried to access the 0 index, but ListObject types only support string keys. "
                "(HINT: List calls return an object with a 'data' (which is the data array). "
                "You likely want to call .data[0])"
            )

    return _ListObject(data)


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

    def test_handler_crash_rolls_back_and_returns_500(self):
        event = make_event(
            "customer.subscription.created", "evt_crash", make_subscription()
        )
        payload = json.dumps(event).encode()
        ArtistSubscription.objects.create(
            artist=self.artist, stripe_customer_id="cus_123"
        )
        self.artist.is_active = False
        self.artist.save(update_fields=["is_active", "updated_at"])

        def raiser(event_dict):
            raise RuntimeError("boom")

        self.client.raise_request_exception = False
        with patch.dict(
            "subscriptions.webhooks.HANDLERS",
            {"customer.subscription.created": raiser},
        ):
            response = self.post(payload)
        self.assertEqual(response.status_code, 500)
        self.assertFalse(StripeEvent.objects.filter(event_id="evt_crash").exists())
        self.artist.refresh_from_db()
        self.assertFalse(self.artist.is_active)

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

    def test_open_portal_redirects_to_portal_url(self):
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
                self._action_url(self.artist, "open-portal")
            )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "https://billing.stripe.com/p/session")

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

    def test_sync_from_stripe_with_listobject_reconciles_state(self):
        """ListObject-shaped mock with one active sub must succeed (real SDK shape).

        Replicates ``stripe/_list_object.py:99`` guard: ``subs[0]`` would raise
        ``KeyError``; the fix must use ``subs.data[0]``. Proves the previous bug.
        """
        self.client.force_login(self.user)
        sub = ArtistSubscription.objects.create(
            artist=self.artist,
            status=ArtistSubscription.Status.PENDING,
            stripe_customer_id="cus_123",
        )
        self.artist.is_active = False
        self.artist.save(update_fields=["is_active"])
        lo = _make_list_object([make_subscription(status="active", period_end=future_epoch())])
        with patch(
            "artworks.admin.stripe_client.fetch_customer",
            return_value=type("C", (), {"email": "a@x.com"}),
        ), patch(
            "artworks.admin.stripe_client.list_subscriptions",
            return_value=lo,
        ):
            response = self.client.get(self._action_url(self.artist, "sync-from-stripe"))
        self.assertEqual(response.status_code, 302)
        sub.refresh_from_db()
        self.assertEqual(sub.status, ArtistSubscription.Status.ACTIVE)
        self.assertEqual(sub.customer_email, "a@x.com")
        self.assertIsNotNone(sub.last_synced_at)
        self.artist.refresh_from_db()
        self.assertTrue(self.artist.is_active)

    def test_sync_from_stripe_with_listobject_empty_sets_canceled(self):
        """ListObject with ``data == []`` must be treated as empty (no crash)."""
        self.client.force_login(self.user)
        sub = ArtistSubscription.objects.create(
            artist=self.artist,
            status=ArtistSubscription.Status.PENDING,
            stripe_customer_id="cus_123",
        )
        lo = _make_list_object([])
        with patch(
            "artworks.admin.stripe_client.fetch_customer",
            return_value=type("C", (), {"email": "a@x.com"}),
        ), patch(
            "artworks.admin.stripe_client.list_subscriptions",
            return_value=lo,
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
        self.assertRegex(
            str(response.content),
            r'href="[^"]*open-portal/"[^>]*target="_blank"',
        )
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


@override_settings(STRIPE_WEBHOOK_SECRET=WEBHOOK_SECRET)
class WebhookSpecTest(ArtistTestBase):
    """Spec scenarios not covered by the larger WebhookTest class."""

    def test_replay_after_handler_crash_is_fresh_run(self):
        """A duplicate `event_id` after a handler crash must re-enter the handler.

        The unique index is the idempotency lock; the StripeEvent INSERT shares
        the handler's atomic block, so on crash the whole transaction rolls back
        and Stripe's retry sees no row and re-runs the handler as fresh.
        """
        event = make_event(
            "customer.subscription.created", "evt_retry", make_subscription()
        )
        payload = json.dumps(event).encode()

        ArtistSubscription.objects.create(
            artist=self.artist, stripe_customer_id="cus_123"
        )
        self.artist.is_active = False
        self.artist.save(update_fields=["is_active", "updated_at"])

        def raiser(event_dict):
            raise RuntimeError("boom")

        self.client.raise_request_exception = False
        with patch.dict(
            "subscriptions.webhooks.HANDLERS",
            {"customer.subscription.created": raiser},
        ):
            first = self.client.post(
                "/webhooks/stripe/",
                data=payload,
                content_type="application/json",
                HTTP_STRIPE_SIGNATURE=stripe_signature(payload),
            )
        self.assertEqual(first.status_code, 500)
        self.artist.refresh_from_db()
        self.assertFalse(self.artist.is_active)
        self.assertFalse(StripeEvent.objects.filter(event_id="evt_retry").exists())

        with patch.dict(
            "subscriptions.webhooks.HANDLERS",
            {
                "customer.subscription.created": _handle_subscription_created,
            },
        ):
            second = self.client.post(
                "/webhooks/stripe/",
                data=payload,
                content_type="application/json",
                HTTP_STRIPE_SIGNATURE=stripe_signature(payload),
            )
        self.assertEqual(second.status_code, 200)
        self.artist.refresh_from_db()
        self.assertTrue(self.artist.is_active)
        record = StripeEvent.objects.get(event_id="evt_retry")
        self.assertIsNotNone(record.processed_at)
        self.assertEqual(record.error, "")

    def test_subscription_event_with_no_matching_artist_is_noop(self):
        """An event whose customer id matches no ArtistSubscription is audit-only."""
        event = make_event(
            "customer.subscription.created",
            "evt_unknown_cus",
            make_subscription(),  # cus_123 — never created locally
        )
        payload = json.dumps(event).encode()
        response = self.client.post(
            "/webhooks/stripe/",
            data=payload,
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE=stripe_signature(payload),
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ArtistSubscription.objects.count(), 0)
        record = StripeEvent.objects.get(event_id="evt_unknown_cus")
        self.assertEqual(record.error, "")
        self.assertIsNotNone(record.processed_at)

    def test_open_portal_without_stripe_customer_id_warns_and_skips_api(self):
        """The endpoint must defend when `signup_url` exists but `stripe_customer_id` is empty.

        Unfold's `has_open_portal_permission` hides the button in this state, but the
        endpoint itself MUST still refuse to call the Stripe API if hit directly
        (e.g. by a staff member pasting the URL).
        """
        self.client.force_login(self.user)
        ArtistSubscription.objects.create(
            artist=self.artist,
            signup_url="https://checkout.stripe.com/c/leftover",
            signup_url_expires_at=timezone.now() + timedelta(hours=1),
        )
        with patch(
            "artworks.admin.stripe_client.create_billing_portal_session"
        ) as create_portal:
            response = self.client.get(self._action_url(self.artist, "open-portal"))
        self.assertEqual(response.status_code, 302)
        create_portal.assert_not_called()
        msgs = [str(m) for m in get_messages(response.wsgi_request)]
        self.assertTrue(
            any("Aún no se generó un link" in m for m in msgs),
            f"Expected a warning about missing link, got: {msgs}",
        )


class FormTest(TestCase):
    def test_amount_zero_rejected(self):
        plan = BillingPlan.get_solo()
        form = BillingPlanForm(data={
            "name": "Membresía Enredarte",
            "amount": "0",
            "currency": "MXN",
            "interval": "month",
            "grace_period_days": 3,
            "is_active_for_new_signups": True,
        }, instance=plan)
        self.assertFalse(form.is_valid())

    def test_amount_negative_rejected(self):
        plan = BillingPlan.get_solo()
        form = BillingPlanForm(data={
            "name": "Membresía Enredarte",
            "amount": "-1",
            "currency": "MXN",
            "interval": "month",
            "grace_period_days": 3,
            "is_active_for_new_signups": True,
        }, instance=plan)
        self.assertFalse(form.is_valid())

    def test_missing_amount_rejected(self):
        plan = BillingPlan.get_solo()
        form = BillingPlanForm(data={
            "name": "Membresía Enredarte",
            "currency": "MXN",
            "interval": "month",
            "grace_period_days": 3,
            "is_active_for_new_signups": True,
        }, instance=plan)
        self.assertFalse(form.is_valid())

    def test_invalid_currency_rejected(self):
        plan = BillingPlan.get_solo()
        form = BillingPlanForm(data={
            "name": "Membresía Enredarte",
            "amount": "299.00",
            "currency": "JPY",
            "interval": "month",
            "grace_period_days": 3,
            "is_active_for_new_signups": True,
        }, instance=plan)
        self.assertFalse(form.is_valid())

    def test_invalid_interval_rejected(self):
        plan = BillingPlan.get_solo()
        form = BillingPlanForm(data={
            "name": "Membresía Enredarte",
            "amount": "299.00",
            "currency": "MXN",
            "interval": "year",
            "grace_period_days": 3,
            "is_active_for_new_signups": True,
        }, instance=plan)
        self.assertFalse(form.is_valid())

    def test_valid_accepted(self):
        plan = BillingPlan.get_solo()
        form = BillingPlanForm(data={
            "name": "Membresía Enredarte",
            "amount": "299.00",
            "currency": "MXN",
            "interval": "month",
            "grace_period_days": 3,
            "is_active_for_new_signups": True,
        }, instance=plan)
        self.assertTrue(form.is_valid(), form.errors)


class EnsureStripePriceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser("admin2", "admin2@x.com", "x")
        self.plan = BillingPlan.get_solo()
        self.plan.amount = Decimal("299.00")
        self.plan.currency = "MXN"
        self.plan.interval = "month"
        self.plan.stripe_product_id = "prod_old"
        self.plan.stripe_price_id = "price_old"
        self.plan.save()

    def test_idempotent_no_stripe_calls(self):
        from subscriptions.services import plan_sync

        # Persisted row already has same values
        self.plan.amount = Decimal("299.00")
        self.plan.currency = "MXN"
        self.plan.interval = "month"
        with patch("subscriptions.services.stripe_client.get_or_create_product") as mock_product, \
             patch("subscriptions.services.stripe_client.create_price") as mock_create, \
             patch("subscriptions.services.stripe_client.set_product_default_price") as mock_set_default, \
             patch("subscriptions.services.stripe_client.archive_price") as mock_archive:
            result = plan_sync.ensure_stripe_price(self.plan, user=self.user)
            mock_product.assert_not_called()
            mock_create.assert_not_called()
            mock_set_default.assert_not_called()
            mock_archive.assert_not_called()
        self.assertEqual(BillingPlanPriceHistory.objects.count(), 0)

    def test_first_save_creates_product_and_price(self):
        from subscriptions.services import plan_sync

        self.plan.stripe_price_id = ""
        self.plan.stripe_product_id = ""
        self.plan.amount = Decimal("299.00")
        self.plan.save(update_fields=["stripe_price_id", "stripe_product_id", "amount"])
        with patch("subscriptions.services.stripe_client.get_or_create_product",
                   return_value=type("P", (), {"id": "prod_new"})), \
             patch("subscriptions.services.stripe_client.create_price",
                   return_value=type("P2", (), {"id": "price_new"})), \
             patch("subscriptions.services.stripe_client.set_product_default_price") as mock_set_default, \
             patch("subscriptions.services.stripe_client.archive_price") as mock_archive:
            result = plan_sync.ensure_stripe_price(self.plan, user=self.user)
            mock_set_default.assert_called_once_with("prod_new", "price_new")
            mock_archive.assert_not_called()
        self.assertEqual(result.stripe_price_id, "price_new")
        self.assertEqual(result.stripe_product_id, "prod_new")
        history = BillingPlanPriceHistory.objects.get()
        self.assertEqual(history.old_stripe_price_id, "")
        self.assertEqual(history.new_stripe_price_id, "price_new")
        self.assertFalse(history.old_price_archived)

    def test_amount_change_creates_price_and_archives(self):
        from subscriptions.services import plan_sync

        self.plan.amount = Decimal("349.00")
        # keep persisted old amount 299, but plan object now 349
        # Ensure persisted row still 299 so change is detected
        # Our plan object has 349, DB has 299
        with patch("subscriptions.services.stripe_client.get_or_create_product",
                   return_value=type("P", (), {"id": "prod_old"})), \
             patch("subscriptions.services.stripe_client.create_price",
                   return_value=type("P2", (), {"id": "price_new2"})), \
             patch("subscriptions.services.stripe_client.set_product_default_price") as mock_set_default, \
             patch("subscriptions.services.stripe_client.archive_price") as mock_archive:
            plan_sync.ensure_stripe_price(self.plan, user=self.user)
            mock_set_default.assert_called_once_with("prod_old", "price_new2")
            mock_archive.assert_called_once_with("price_old")
        history = BillingPlanPriceHistory.objects.get()
        self.assertEqual(history.old_stripe_price_id, "price_old")
        self.assertEqual(history.new_stripe_price_id, "price_new2")
        self.assertTrue(history.old_price_archived)
        self.plan.refresh_from_db()
        self.assertEqual(self.plan.stripe_price_id, "price_new2")

    def test_stripe_error_on_product_propagates_and_no_save(self):
        from subscriptions.services import plan_sync

        self.plan.amount = Decimal("400.00")
        with patch("subscriptions.services.stripe_client.get_or_create_product",
                   side_effect=stripe_lib.error.StripeError("boom")):
            with self.assertRaises(stripe_lib.error.StripeError):
                plan_sync.ensure_stripe_price(self.plan, user=self.user)
        self.assertEqual(BillingPlanPriceHistory.objects.count(), 0)
        # stripe_price_id unchanged
        self.plan.refresh_from_db()
        self.assertEqual(self.plan.stripe_price_id, "price_old")

    def test_stripe_error_on_archive_propagates_no_history(self):
        from subscriptions.services import plan_sync

        self.plan.amount = Decimal("400.00")
        with patch("subscriptions.services.stripe_client.get_or_create_product",
                   return_value=type("P", (), {"id": "prod_old"})), \
             patch("subscriptions.services.stripe_client.create_price",
                   return_value=type("P2", (), {"id": "price_new_err"})), \
             patch("subscriptions.services.stripe_client.set_product_default_price"), \
             patch("subscriptions.services.stripe_client.archive_price",
                   side_effect=stripe_lib.error.StripeError("archive boom")):
            with self.assertRaises(stripe_lib.error.StripeError):
                plan_sync.ensure_stripe_price(self.plan, user=self.user)
        self.assertEqual(BillingPlanPriceHistory.objects.count(), 0)
        self.plan.refresh_from_db()
        self.assertEqual(self.plan.stripe_price_id, "price_old")

    def test_stripe_error_on_set_default_propagates_no_history(self):
        from subscriptions.services import plan_sync

        self.plan.amount = Decimal("400.00")
        with patch("subscriptions.services.stripe_client.get_or_create_product",
                   return_value=type("P", (), {"id": "prod_old"})), \
             patch("subscriptions.services.stripe_client.create_price",
                   return_value=type("P2", (), {"id": "price_new_err"})), \
             patch("subscriptions.services.stripe_client.set_product_default_price",
                   side_effect=stripe_lib.error.StripeError("default boom")):
            with self.assertRaises(stripe_lib.error.StripeError):
                plan_sync.ensure_stripe_price(self.plan, user=self.user)
        self.assertEqual(BillingPlanPriceHistory.objects.count(), 0)
        self.plan.refresh_from_db()
        self.assertEqual(self.plan.stripe_price_id, "price_old")


class LivePreviewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser("admin", "admin@x.com", "x")
        self.client.force_login(self.user)
        self.plan = BillingPlan.get_solo()
        self.plan.amount = Decimal("299.00")
        self.plan.currency = "MXN"
        self.plan.interval = "month"
        self.plan.stripe_price_id = "price_test"
        self.plan.save()

    def test_change_view_shows_confirmed(self):
        fake_price = type("P", (), {
            "id": "price_test",
            "unit_amount": 29900,
            "currency": "mxn",
            "recurring": {"interval": "month"},
        })
        with patch("subscriptions.services.stripe_client.retrieve_price", return_value=fake_price):
            response = self.client.get(f"/admin/subscriptions/billingplan/{self.plan.pk}/change/")
        self.assertEqual(response.status_code, 200)
        # extra_context flows into admin display via _stripe_live_summary
        self.assertContains(response, "Confirmado por Stripe")
        self.assertContains(response, "299.00")
        self.assertContains(response, "MXN")

    def test_change_view_handles_retrieve_failure(self):
        with patch("subscriptions.services.stripe_client.retrieve_price",
                   side_effect=Exception("network")):
            response = self.client.get(f"/admin/subscriptions/billingplan/{self.plan.pk}/change/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "(no se pudo confirmar)")


class BillingBlockedTest(ArtistTestBase):
    def test_blocked_by_missing_price_id_uses_new_message(self):
        from artworks.admin import _billing_blocked

        BillingPlan.get_solo().save()
        BillingPlan.objects.update(stripe_price_id="")
        msg = _billing_blocked(self.artist)
        self.assertIsNotNone(msg)
        self.assertIn("Configura el precio", str(msg))

    def test_not_blocked_when_price_id_present(self):
        from artworks.admin import _billing_blocked

        BillingPlan.get_solo().save()
        BillingPlan.objects.update(stripe_price_id="price_test", is_active_for_new_signups=True)
        msg = _billing_blocked(self.artist)
        self.assertIsNone(msg)

    def test_blocked_by_inactive_signups(self):
        from artworks.admin import _billing_blocked

        BillingPlan.get_solo().save()
        BillingPlan.objects.update(stripe_price_id="price_test", is_active_for_new_signups=False)
        msg = _billing_blocked(self.artist)
        self.assertIsNotNone(msg)
        self.assertIn("pausadas", str(msg))

    def test_blocked_by_missing_email(self):
        from artworks.admin import _billing_blocked

        artist_no_email = self.make_artist("Sin mail", email="")
        BillingPlan.get_solo().save()
        BillingPlan.objects.update(stripe_price_id="price_test")
        msg = _billing_blocked(artist_no_email)
        self.assertIsNotNone(msg)
        self.assertIn("correo", str(msg).lower())
