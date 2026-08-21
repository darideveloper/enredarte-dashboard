from rest_framework import serializers


def _translation_value(obj, language, attr):
    translations = list(obj.translations.all())
    row = next((t for t in translations if t.language == language), None)
    row = row or (translations[0] if translations else None)
    return getattr(row, attr) if row else obj.slug


def _name_es(obj):
    return _translation_value(obj, "es", "name")


def _name_en(obj):
    return _translation_value(obj, "en", "name")


def _title_es(obj):
    return _translation_value(obj, "es", "title")


def _title_en(obj):
    return _translation_value(obj, "en", "title")


def _primary_image(obj):
    images = list(obj.images.all())
    return next((i for i in images if i.is_primary), None) or (images[0] if images else None)


class RefSerializer(serializers.Serializer):
    """Reference entry for taxonomy terms and locations: id, slug, bilingual name."""

    id = serializers.IntegerField()
    slug = serializers.CharField()
    name_es = serializers.SerializerMethodField()
    name_en = serializers.SerializerMethodField()

    def get_name_es(self, obj):
        return _name_es(obj)

    def get_name_en(self, obj):
        return _name_en(obj)


class ArtistRefSerializer(serializers.Serializer):
    """Artist entry: id, slug, name (language-independent) and location reference."""

    id = serializers.IntegerField()
    slug = serializers.CharField()
    name_es = serializers.SerializerMethodField()
    name_en = serializers.SerializerMethodField()
    location_id = serializers.IntegerField(allow_null=True)

    def get_name_es(self, obj):
        return obj.name

    def get_name_en(self, obj):
        return obj.name


class ArtworkSerializer(serializers.Serializer):
    """Denormalized artwork entry for client-side faceting."""

    id = serializers.IntegerField()
    slug = serializers.CharField()
    title_es = serializers.SerializerMethodField()
    title_en = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    image_alt_es = serializers.SerializerMethodField()
    image_alt_en = serializers.SerializerMethodField()
    artist_id = serializers.IntegerField()
    year = serializers.IntegerField()
    dimensions = serializers.CharField()
    price_mxn = serializers.DecimalField(max_digits=10, decimal_places=2, coerce_to_string=False)
    price_usd = serializers.DecimalField(max_digits=10, decimal_places=2, coerce_to_string=False)
    disciplines = serializers.SerializerMethodField()
    techniques = serializers.SerializerMethodField()
    themes = serializers.SerializerMethodField()
    formats = serializers.SerializerMethodField()
    scales = serializers.SerializerMethodField()

    def get_title_es(self, obj):
        return _title_es(obj)

    def get_title_en(self, obj):
        return _title_en(obj)

    def get_image(self, obj):
        img = _primary_image(obj)
        return img.image.url if img else None

    def get_image_alt_es(self, obj):
        img = _primary_image(obj)
        return (img.alt_es or _title_es(obj)) if img else None

    def get_image_alt_en(self, obj):
        img = _primary_image(obj)
        return (img.alt_en or _title_en(obj)) if img else None

    def _ids(self, obj, field):
        return [item.id for item in getattr(obj, field).all()]

    def get_disciplines(self, obj):
        return self._ids(obj, "disciplines")

    def get_techniques(self, obj):
        return self._ids(obj, "techniques")

    def get_themes(self, obj):
        return self._ids(obj, "themes")

    def get_formats(self, obj):
        return self._ids(obj, "formats")

    def get_scales(self, obj):
        return self._ids(obj, "scales")
