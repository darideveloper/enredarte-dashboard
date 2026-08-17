from rest_framework import serializers

from artworks.models import (
    ArtCurator,
    Artist,
    ArtistSocialLink,
    Artwork,
    ArtworkGallery,
    ArtworkImage,
    Discipline,
    Format,
    Gallery,
    Location,
    Scale,
    Technique,
    Theme,
)
from utils.media import get_media_url


def _build_translation_dict(translations, fields):
    return {
        t.language: {f: getattr(t, f) for f in fields if getattr(t, f, None)}
        for t in translations
    }


def _absolute_url(field_value):
    return get_media_url(field_value) if field_value else None


class RefSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    slug = serializers.CharField()


class ArtistSocialLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArtistSocialLink
        fields = ["id", "platform", "url"]


class ArtworkImageSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = ArtworkImage
        fields = ["id", "image", "alt_es", "alt_en", "is_primary", "sort_order"]

    def get_image(self, obj):
        return _absolute_url(obj.image)


class ArtworkGalleryLinkSerializer(serializers.ModelSerializer):
    gallery = RefSerializer()

    class Meta:
        model = ArtworkGallery
        fields = ["id", "gallery", "sort_order"]


class GalleryArtworkLinkSerializer(serializers.ModelSerializer):
    artwork = RefSerializer()

    class Meta:
        model = ArtworkGallery
        fields = ["id", "artwork", "sort_order"]


class ArtistSerializer(serializers.ModelSerializer):
    photo = serializers.SerializerMethodField()
    location = RefSerializer(allow_null=True)
    translations = serializers.SerializerMethodField()
    social_links = ArtistSocialLinkSerializer(many=True, read_only=True)

    class Meta:
        model = Artist
        fields = [
            "id", "slug", "is_active", "sort_order", "created_at", "updated_at",
            "name", "email", "website", "photo", "birth_year", "death_year",
            "location", "translations", "social_links",
        ]

    def get_photo(self, obj):
        return _absolute_url(obj.photo)

    def get_translations(self, obj):
        return _build_translation_dict(obj.translations.all(), ["bio"])


class ArtCuratorSerializer(serializers.ModelSerializer):
    photo = serializers.SerializerMethodField()
    translations = serializers.SerializerMethodField()

    class Meta:
        model = ArtCurator
        fields = [
            "id", "slug", "is_active", "sort_order", "created_at", "updated_at",
            "name", "email", "website", "photo", "translations",
        ]

    def get_photo(self, obj):
        return _absolute_url(obj.photo)

    def get_translations(self, obj):
        return _build_translation_dict(obj.translations.all(), ["bio"])


class LocationSerializer(serializers.ModelSerializer):
    translations = serializers.SerializerMethodField()

    class Meta:
        model = Location
        fields = [
            "id", "slug", "is_active", "sort_order", "created_at", "updated_at",
            "translations",
        ]

    def get_translations(self, obj):
        return _build_translation_dict(obj.translations.all(), ["name"])


class GallerySerializer(serializers.ModelSerializer):
    logo = serializers.SerializerMethodField()
    curator = RefSerializer(allow_null=True)
    translations = serializers.SerializerMethodField()
    artwork_links = GalleryArtworkLinkSerializer(many=True, read_only=True)

    class Meta:
        model = Gallery
        fields = [
            "id", "slug", "is_active", "sort_order", "created_at", "updated_at",
            "logo", "curator", "translations", "artwork_links",
        ]

    def get_logo(self, obj):
        return _absolute_url(obj.logo)

    def get_translations(self, obj):
        return _build_translation_dict(obj.translations.all(), ["name", "description"])


class _TaxonomySerializer(serializers.ModelSerializer):
    translations = serializers.SerializerMethodField()

    class Meta:
        fields = [
            "id", "slug", "is_active", "sort_order", "created_at", "updated_at",
            "translations",
        ]

    def get_translations(self, obj):
        return _build_translation_dict(obj.translations.all(), ["name"])


class DisciplineSerializer(_TaxonomySerializer):
    class Meta(_TaxonomySerializer.Meta):
        model = Discipline


class TechniqueSerializer(_TaxonomySerializer):
    class Meta(_TaxonomySerializer.Meta):
        model = Technique


class ThemeSerializer(_TaxonomySerializer):
    class Meta(_TaxonomySerializer.Meta):
        model = Theme


class FormatSerializer(_TaxonomySerializer):
    class Meta(_TaxonomySerializer.Meta):
        model = Format


class ScaleSerializer(_TaxonomySerializer):
    class Meta(_TaxonomySerializer.Meta):
        model = Scale


class ArtworkSerializer(serializers.ModelSerializer):
    artist = RefSerializer()
    disciplines = RefSerializer(many=True)
    techniques = RefSerializer(many=True)
    themes = RefSerializer(many=True)
    formats = RefSerializer(many=True)
    scales = RefSerializer(many=True)
    price_mxn = serializers.DecimalField(max_digits=10, decimal_places=2, coerce_to_string=False)
    price_usd = serializers.DecimalField(max_digits=10, decimal_places=2, coerce_to_string=False)
    translations = serializers.SerializerMethodField()
    images = ArtworkImageSerializer(many=True, read_only=True)
    gallery_links = ArtworkGalleryLinkSerializer(many=True, read_only=True)

    class Meta:
        model = Artwork
        fields = [
            "id", "slug", "is_active", "sort_order", "created_at", "updated_at",
            "artist", "year", "dimensions",
            "disciplines", "techniques", "themes", "formats", "scales",
            "price_mxn", "price_usd", "status", "is_highlighted", "views_count",
            "translations", "images", "gallery_links",
        ]

    def get_translations(self, obj):
        return _build_translation_dict(obj.translations.all(), ["title", "description"])
