"""Orchestrator for BillingPlan -> Stripe price sync."""

from django.db import transaction
from django.utils import timezone

from subscriptions.models import BillingPlanPriceHistory
from subscriptions.services import stripe_client


def ensure_stripe_price(plan, user=None):
    """Ensure a Stripe Price exists for ``plan``; idempotent.

    If ``plan.stripe_price_id`` is set and the (amount, currency, interval)
    tuple matches the persisted row, no Stripe calls are made.

    Otherwise creates (or reuses) a Stripe Product, creates a new Price,
    archives the old Price if any, writes a ``BillingPlanPriceHistory`` row,
    and updates ``plan``'s auto-managed fields.
    """
    # Idempotence check against persisted row
    if plan.pk is not None and plan.stripe_price_id:
        try:
            existing = plan.__class__.objects.get(pk=plan.pk)
        except plan.__class__.DoesNotExist:
            existing = None
        if existing is not None:
            if (
                existing.stripe_price_id == plan.stripe_price_id
                and existing.amount == plan.amount
                and existing.currency == plan.currency
                and existing.interval == plan.interval
            ):
                return plan

    old_price_id = plan.stripe_price_id or ""
    old_product_id = plan.stripe_product_id or ""

    # 1. Get or create Stripe product (re-raise StripeError)
    product = stripe_client.get_or_create_product(
        name=plan.name, existing_id=old_product_id
    )
    product_id = product.id if hasattr(product, "id") else product.get("id")

    # 2. Create new Stripe price
    new_price = stripe_client.create_price(
        product_id=product_id,
        amount_decimal=plan.amount,
        currency=plan.currency,
        interval=plan.interval,
    )
    new_price_id = new_price.id if hasattr(new_price, "id") else new_price.get("id")

    # 3. Repoint product default_price before archiving (Stripe blocks
    # archiving a price that is the product's default_price).
    # Always point product to the new price so Dashboard stays consistent.
    # Must happen before archive, otherwise InvalidRequestError.
    stripe_client.set_product_default_price(product_id, new_price_id)

    # 4. Archive old price if present
    if old_price_id:
        stripe_client.archive_price(old_price_id)

    # 5. Create history row + update plan atomically
    with transaction.atomic():
        BillingPlanPriceHistory.objects.create(
            billing_plan=plan,
            old_stripe_price_id=old_price_id,
            new_stripe_price_id=new_price_id,
            amount=plan.amount,
            currency=plan.currency,
            interval=plan.interval,
            old_price_archived=bool(old_price_id),
            changed_by=user,
        )

        plan.stripe_product_id = product_id
        plan.stripe_price_id = new_price_id
        plan.last_synced_stripe_at = timezone.now()
        # BillingPlan is a SingletonModel without TimeStampedModel, so it has
        # no `updated_at` field. Task spec lists it, but we intentionally omit it.
        plan.save(update_fields=["stripe_product_id", "stripe_price_id", "last_synced_stripe_at"])

    return plan
