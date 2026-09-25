from django.conf import settings
from django.db import transaction
from django.db.models import F, Prefetch
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from artworks.models import (
    ArtCurator,
    Artist,
    ArtistSocialLink,
    Artwork,
    ArtworkGallery,
    ArtworkImage,
    ArtworkOrder,
    ArtworkOrderStatus,
    ArtworkStatus,
    Discipline,
    Format,
    Gallery,
    Location,
    Scale,
    Technique,
    Theme,
)
from artworks.serializers import (
    ArtCuratorSerializer,
    ArtistSerializer,
    ArtworkSerializer,
    BuyArtworkSerializer,
    DeliveryInfoSerializer,
    DisciplineSerializer,
    FormatSerializer,
    GallerySerializer,
    LocationSerializer,
    OrderSummarySerializer,
    ScaleSerializer,
    TechniqueSerializer,
    ThemeSerializer,
)
from artworks.services import apply_paid_transition, reconcile_stale_reservations
from artworks import sale_notifications
from core.mail_utils import send_best_effort


class ArtistViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ArtistSerializer

    def get_queryset(self):
        return Artist.objects.filter(is_active=True).select_related("location").prefetch_related(
            Prefetch("social_links", queryset=ArtistSocialLink.objects.filter(is_active=True)),
            "translations",
        ).order_by("-created_at")


class ArtCuratorViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ArtCurator.objects.filter(is_active=True).prefetch_related(
        "translations"
    ).order_by("-created_at")
    serializer_class = ArtCuratorSerializer


class LocationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Location.objects.filter(is_active=True).prefetch_related(
        "translations"
    ).order_by("-created_at")
    serializer_class = LocationSerializer


class GalleryViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = GallerySerializer

    def get_queryset(self):
        return Gallery.objects.filter(is_active=True).select_related("curator").prefetch_related(
            Prefetch(
                "artwork_links",
                queryset=ArtworkGallery.objects.filter(
                    is_active=True, artwork__is_active=True
                ).select_related("artwork").order_by("sort_order"),
            ),
            "translations",
        ).order_by("-created_at")


class _TaxonomyViewSet(viewsets.ReadOnlyModelViewSet):
    def get_queryset(self):
        return self.model.objects.filter(is_active=True).prefetch_related(
            "translations"
        ).order_by("-created_at")


class DisciplineViewSet(_TaxonomyViewSet):
    model = Discipline
    serializer_class = DisciplineSerializer


class TechniqueViewSet(_TaxonomyViewSet):
    model = Technique
    serializer_class = TechniqueSerializer


class ThemeViewSet(_TaxonomyViewSet):
    model = Theme
    serializer_class = ThemeSerializer


class FormatViewSet(_TaxonomyViewSet):
    model = Format
    serializer_class = FormatSerializer


class ScaleViewSet(_TaxonomyViewSet):
    model = Scale
    serializer_class = ScaleSerializer


class ArtworkViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ArtworkSerializer

    def get_throttles(self):
        if getattr(self, "action", None) == "buy":
            # ScopedRateThrottle reads the scope from the view (it is not a
            # valid @action kwarg, so it is set here before the check runs).
            self.throttle_scope = "artwork_buys"
        elif getattr(self, "action", None) == "visit":
            self.throttle_scope = "artwork_views"
        elif getattr(self, "action", None) == "artwork_status":
            self.throttle_scope = "artwork_status"
        return super().get_throttles()

    def get_queryset(self):
        return Artwork.objects.filter(
            is_active=True, artist__is_active=True
        ).select_related("artist").prefetch_related(
            Prefetch("disciplines", queryset=Discipline.objects.filter(is_active=True)),
            Prefetch("techniques", queryset=Technique.objects.filter(is_active=True)),
            Prefetch("themes", queryset=Theme.objects.filter(is_active=True)),
            Prefetch("formats", queryset=Format.objects.filter(is_active=True)),
            Prefetch("scales", queryset=Scale.objects.filter(is_active=True)),
            Prefetch(
                "images",
                queryset=ArtworkImage.objects.filter(is_active=True).order_by("sort_order"),
            ),
            Prefetch(
                "gallery_links",
                queryset=ArtworkGallery.objects.filter(
                    is_active=True, gallery__is_active=True
                ).select_related("gallery").order_by("sort_order"),
            ),
            "translations",
        ).order_by("-created_at")

    @action(
        detail=True, methods=["post"], url_path="buy",
        permission_classes=[AllowAny], authentication_classes=[],
        throttle_classes=[ScopedRateThrottle],
    )
    def buy(self, request, pk=None):
        from core.stripe_utils import epoch_to_datetime
        from artworks import stripe_orders

        serializer = BuyArtworkSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"status": "error", "message": "Invalid data", "data": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        currency = serializer.validated_data["currency"]
        email = serializer.validated_data["email"].strip().lower()
        public_url = (getattr(settings, "PUBLIC_SITE_URL", "") or "").rstrip("/")
        if not public_url:
            return Response(
                {"status": "error", "message": "Ventas no configuradas (PUBLIC_SITE_URL).", "data": {}},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        try:
            # Lazy reconcile (phase 1, no lock): a stale RESERVED hold from a
            # closed tab or abandoned Checkout self-heals here — verified
            # against Stripe, never on clock alone. The atomic block below
            # re-reads the row, so it sees the post-transition state.
            probe = Artwork.objects.filter(slug=pk, is_active=True).only("status").first()
            if probe is not None and probe.status == ArtworkStatus.RESERVED:
                reconcile_stale_reservations(probe)
            with transaction.atomic():
                try:
                    artwork = Artwork.objects.select_for_update().get(slug=pk, is_active=True)
                except Artwork.DoesNotExist:
                    return Response(
                        {"status": "error", "message": "Not found.", "data": {}},
                        status=status.HTTP_404_NOT_FOUND,
                    )
                if artwork.status == ArtworkStatus.RESERVED:
                    pending = (
                        artwork.orders.filter(status=ArtworkOrderStatus.PENDING_PAYMENT)
                        .order_by("-created_at").first()
                    )
                    if (
                        pending
                        and pending.session_expires_at
                        and pending.session_expires_at > timezone.now()
                        and pending.buyer_email.lower() == email
                    ):
                        return Response({"checkout_url": pending.checkout_url}, status=status.HTTP_200_OK)
                    return Response(
                        {"status": "error", "message": "Reserva en curso para esta obra.", "data": {}},
                        status=status.HTTP_409_CONFLICT,
                    )
                if artwork.status != ArtworkStatus.AVAILABLE:
                    return Response(
                        {"status": "error", "message": "Obra no disponible.", "data": {}},
                        status=status.HTTP_409_CONFLICT,
                    )
                artwork.status = ArtworkStatus.RESERVED
                artwork.save(update_fields=["status", "updated_at"])
                amount = artwork.price_mxn if currency == "mxn" else artwork.price_usd
                order = ArtworkOrder.objects.create(
                    artwork=artwork, currency=currency, amount=amount, buyer_email=email,
                )
                success_url = f"{public_url}/compra-exitosa/?order={order.slug}"
                cancel_url = f"{public_url}/compra-cancelada/"
                try:
                    session = stripe_orders.create_artwork_checkout_session(
                        amount=amount, currency=currency, customer_email=email,
                        metadata={"kind": "artwork_order", "order": order.slug},
                        success_url=success_url, cancel_url=cancel_url,
                        expires_at=timezone.now() + timezone.timedelta(minutes=30),
                        product_name=artwork.translated_title(),
                    )
                except Exception:
                    raise
                order.stripe_checkout_session_id = getattr(session, "id", "") or session.get("id", "")
                order.checkout_url = getattr(session, "url", "") or session.get("url", "")
                raw_exp = getattr(session, "expires_at", None)
                if raw_exp is None and isinstance(session, dict):
                    raw_exp = session.get("expires_at")
                order.session_expires_at = epoch_to_datetime(raw_exp) if raw_exp else None
                order.save(update_fields=[
                    "stripe_checkout_session_id", "checkout_url",
                    "session_expires_at", "updated_at",
                ])
        except Exception:
            import logging

            logging.getLogger(__name__).exception("buy checkout failed artwork=%s", pk)
            return Response(
                {"status": "error", "message": "Stripe no respondió.", "data": {}},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        send_best_effort(sale_notifications.send_sale_reserved, order)
        return Response({"checkout_url": order.checkout_url}, status=status.HTTP_201_CREATED)

    @action(
        detail=True, methods=["post"], url_path="visit",
        permission_classes=[AllowAny], authentication_classes=[],
        throttle_classes=[ScopedRateThrottle],
    )
    def visit(self, request, pk=None):
        updated = Artwork.objects.filter(
            slug=pk, is_active=True, artist__is_active=True
        ).update(views_count=F("views_count") + 1)
        if not updated:
            return Response(
                {"status": "error", "message": "Not found.", "data": {}},
                status=status.HTTP_404_NOT_FOUND,
            )
        artwork = Artwork.objects.filter(slug=pk).only("views_count").get()
        return Response({"views_count": artwork.views_count}, status=status.HTTP_200_OK)

    @action(
        detail=True, methods=["get"], url_path="status",
        permission_classes=[AllowAny], authentication_classes=[],
        throttle_classes=[ScopedRateThrottle],
    )
    def artwork_status(self, request, pk=None):
        artwork = Artwork.objects.filter(
            slug=pk, is_active=True, artist__is_active=True
        ).only("slug", "status", "price_mxn", "price_usd", "updated_at").first()
        if artwork is None:
            return Response(
                {"status": "error", "message": "Not found.", "data": {}},
                status=status.HTTP_404_NOT_FOUND,
            )
        if artwork.status == ArtworkStatus.RESERVED:
            # Lazy reconcile (Stripe fetch lock-free, persist under row lock):
            # re-read the post-transition row so the response never goes stale.
            reconcile_stale_reservations(artwork)
            artwork.refresh_from_db()
        response = Response(
            {
                "slug": artwork.slug,
                "status": artwork.status,
                "status_display": artwork.get_status_display(),
                "price_mxn": str(artwork.price_mxn),
                "price_usd": str(artwork.price_usd),
                "updated_at": artwork.updated_at.isoformat().replace("+00:00", "Z"),
            },
            status=status.HTTP_200_OK,
        )
        response["Cache-Control"] = "no-store"
        return response


def _public_order_queryset():
    return ArtworkOrder.objects.select_related("artwork", "artwork__artist").prefetch_related(
        "artwork__images", "artwork__translations",
    )


class OrderSummaryView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "artwork_orders"

    def get(self, request, slug):
        from artworks import stripe_orders

        order = _public_order_queryset().filter(slug=slug).first()
        if order is None or order.status in (
            ArtworkOrderStatus.CANCELLED, ArtworkOrderStatus.REFUNDED,
        ):
            return Response(
                {"status": "error", "message": "Not found.", "data": {}},
                status=status.HTTP_404_NOT_FOUND,
            )
        if order.status == ArtworkOrderStatus.PENDING_PAYMENT:
            try:
                session = stripe_orders.retrieve_checkout_session(order.stripe_checkout_session_id)
                paid = (getattr(session, "payment_status", None)
                        or (session.get("payment_status") if isinstance(session, dict) else None))
            except Exception:
                paid = None
            if paid == "paid":
                pi = getattr(session, "payment_intent", None)
                if pi is None and isinstance(session, dict):
                    pi = session.get("payment_intent")
                details = getattr(session, "customer_details", None)
                if details is None and isinstance(session, dict):
                    details = session.get("customer_details") or {}
                buyer_name = (getattr(details, "name", None)
                              if not isinstance(details, dict) else details.get("name")) or ""
                with transaction.atomic():
                    order = ArtworkOrder.objects.select_for_update().get(pk=order.pk)
                    transitioned = apply_paid_transition(order, str(pi or ""), order.buyer_email, buyer_name or "")
                if transitioned:
                    send_best_effort(sale_notifications.send_sale_paid, order)
                order = _public_order_queryset().get(pk=order.pk)
            else:
                return Response(
                    {"status": "error", "message": "Not found.", "data": {}},
                    status=status.HTTP_404_NOT_FOUND,
                )
        return Response(OrderSummarySerializer(order).data, status=status.HTTP_200_OK)


class OrderDeliveryView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "artwork_orders"

    def post(self, request, slug):
        order = ArtworkOrder.objects.filter(slug=slug).first()
        if order is None:
            return Response(
                {"status": "error", "message": "Not found.", "data": {}},
                status=status.HTTP_404_NOT_FOUND,
            )
        if order.status != ArtworkOrderStatus.PAID_PENDING_DATA:
            return Response(
                {"status": "error", "message": "La orden no espera datos de entrega.", "data": {}},
                status=status.HTTP_409_CONFLICT,
            )
        serializer = DeliveryInfoSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"status": "error", "message": "Invalid data", "data": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        for field, value in serializer.validated_data.items():
            setattr(order, field, value)
        order.status = ArtworkOrderStatus.DATA_COMPLETE
        order.save()
        send_best_effort(sale_notifications.send_sale_delivery_complete, order)
        return Response(OrderSummarySerializer(order).data, status=status.HTTP_200_OK)
