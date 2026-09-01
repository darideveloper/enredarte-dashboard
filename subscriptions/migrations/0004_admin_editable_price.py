# Generated for admin-editable subscription price
import stripe
from decimal import Decimal

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def seed_from_stripe_price_id(apps, schema_editor):
    BillingPlan = apps.get_model("subscriptions", "BillingPlan")
    price_id = getattr(settings, "STRIPE_PRICE_ID", "")
    if not price_id:
        return
    # stripe.api_key is set on import via stripe_client; check directly
    if not getattr(stripe, "api_key", None):
        # Also try settings key
        key = getattr(settings, "STRIPE_SECRET_KEY", "")
        if not key:
            return
        stripe.api_key = key
    if not stripe.api_key:
        return
    try:
        price = stripe.Price.retrieve(price_id)
    except Exception:
        return
    try:
        unit_amount = price.get("unit_amount") if isinstance(price, dict) else getattr(price, "unit_amount", None)
        currency = price.get("currency") if isinstance(price, dict) else getattr(price, "currency", None)
        product = price.get("product") if isinstance(price, dict) else getattr(price, "product", None)
        pid = price.get("id") if isinstance(price, dict) else getattr(price, "id", None)
        # Handle object-style
        if hasattr(price, "unit_amount"):
            unit_amount = price.unit_amount
        if hasattr(price, "currency"):
            currency = price.currency
        if hasattr(price, "product"):
            product = price.product
        if hasattr(price, "id"):
            pid = price.id
        amount = Decimal(unit_amount) / Decimal(100) if unit_amount is not None else Decimal("0")
        currency_val = (currency or "MXN").upper()
        # interval from recurring
        recurring = None
        if isinstance(price, dict):
            recurring = price.get("recurring")
        elif hasattr(price, "recurring"):
            recurring = price.recurring
        interval = "month"
        if isinstance(recurring, dict):
            interval = recurring.get("interval", "month")
        elif recurring and hasattr(recurring, "interval"):
            interval = recurring.interval or "month"
        BillingPlan.objects.all().update(
            amount=amount,
            currency=currency_val,
            interval=interval,
            stripe_product_id=product or "",
            stripe_price_id=pid or price_id,
        )
    except Exception:
        return


class Migration(migrations.Migration):

    dependencies = [
        ("subscriptions", "0003_alter_billingplan_stripe_price_id"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="billingplan",
            name="amount",
            field=models.DecimalField(decimal_places=2, default=0, help_text="Monto a cobrar por período. Debe ser mayor que 0.", max_digits=8, verbose_name="Monto"),
        ),
        migrations.AddField(
            model_name="billingplan",
            name="interval",
            field=models.CharField(choices=[("month", "Mensual")], default="month", help_text="Intervalo de facturación. Actualmente solo mensual.", max_length=10, verbose_name="Periodicidad"),
        ),
        migrations.AddField(
            model_name="billingplan",
            name="stripe_product_id",
            field=models.CharField(blank=True, default="", help_text="Identificador `prod_xxx` gestionado automáticamente. No editar manualmente.", max_length=100, verbose_name="ID de producto en Stripe"),
        ),
        migrations.AddField(
            model_name="billingplan",
            name="last_synced_stripe_at",
            field=models.DateTimeField(blank=True, help_text="Última vez que se creó o archivó un precio en Stripe desde el admin.", null=True, verbose_name="Última sincronización con Stripe"),
        ),
        migrations.AlterField(
            model_name="billingplan",
            name="currency",
            field=models.CharField(choices=[("MXN", "MXN"), ("USD", "USD")], default="MXN", help_text="Moneda del precio. Solo MXN y USD.", max_length=3, verbose_name="Moneda"),
        ),
        migrations.AlterField(
            model_name="billingplan",
            name="stripe_price_id",
            field=models.CharField(blank=True, default="", help_text="Identificador `price_xxx` gestionado automáticamente. No editar manualmente.", max_length=100, verbose_name="ID de precio en Stripe"),
        ),
        migrations.CreateModel(
            name="BillingPlanPriceHistory",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("old_stripe_price_id", models.CharField(blank=True, default="", help_text="Identificador `price_xxx` anterior. Vacío en la primera creación.", max_length=100, verbose_name="ID de precio anterior")),
                ("new_stripe_price_id", models.CharField(help_text="Identificador `price_xxx` recién creado en Stripe.", max_length=100, verbose_name="ID de precio nuevo")),
                ("amount", models.DecimalField(decimal_places=2, help_text="Monto del nuevo precio.", max_digits=8, verbose_name="Monto")),
                ("currency", models.CharField(help_text="Moneda del nuevo precio (MXN o USD).", max_length=3, verbose_name="Moneda")),
                ("interval", models.CharField(help_text="Intervalo del nuevo precio (actualmente solo mensual).", max_length=10, verbose_name="Periodicidad")),
                ("old_price_archived", models.BooleanField(default=True, help_text="Si el precio anterior fue archivado (active=False) en Stripe.", verbose_name="Precio anterior archivado")),
                ("changed_at", models.DateTimeField(auto_now_add=True, help_text="Momento en que se registró el cambio.", verbose_name="Fecha de cambio")),
                ("billing_plan", models.ForeignKey(help_text="Plan al que pertenece este cambio de precio.", on_delete=django.db.models.deletion.CASCADE, related_name="history", to="subscriptions.billingplan", verbose_name="Plan de suscripción")),
                ("changed_by", models.ForeignKey(blank=True, help_text="Usuario que realizó el cambio. Vacío si no hay usuario.", null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name="Modificado por")),
            ],
            options={
                "ordering": ["-changed_at"],
                "verbose_name": "Historial de precio",
                "verbose_name_plural": "Historial de precios",
            },
        ),
        migrations.RunPython(seed_from_stripe_price_id, migrations.RunPython.noop),
    ]
