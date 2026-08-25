# Manual migration: make Artist.email required for the Stripe subscription flow.
#
# Existing artists without an email are backfilled with an empty string and a
# console warning lists them for operator follow-up (the admin form blocks new
# subscription actions until a real email is captured).

from django.db import migrations, models


def backfill_artist_email(apps, schema_editor):
    Artist = apps.get_model("artworks", "Artist")
    affected = list(Artist.objects.filter(email__isnull=True))
    if affected:
        for artist in affected:
            artist.email = ""
        Artist.objects.bulk_update(affected, ["email"])
    if affected:
        names = ", ".join(artist.name for artist in affected)
        print(
            f"\n[WARNING] {len(affected)} artista(s) sin correo electrónico fueron "
            f"rellenados con cadena vacía. Revisa y captura su email: {names}\n"
        )


class Migration(migrations.Migration):

    dependencies = [
        ("artworks", "0009_alter_gallery_is_primary"),
    ]

    operations = [
        migrations.RunPython(backfill_artist_email, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="artist",
            name="email",
            field=models.EmailField(
                help_text="Requerido: Stripe lo usa como identidad del cliente al generar un link de suscripción.",
                verbose_name="Correo electrónico",
            ),
        ),
    ]