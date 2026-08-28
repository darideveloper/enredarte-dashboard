from django.conf import settings
from django.db import migrations


def backfill_stripe_price_id(apps, schema_editor):
    BillingPlan = apps.get_model("subscriptions", "BillingPlan")
    if not settings.STRIPE_PRICE_ID:
        return
    BillingPlan.objects.filter(stripe_price_id="").update(
        stripe_price_id=settings.STRIPE_PRICE_ID
    )


class Migration(migrations.Migration):

    dependencies = [
        ("subscriptions", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(backfill_stripe_price_id, migrations.RunPython.noop),
    ]