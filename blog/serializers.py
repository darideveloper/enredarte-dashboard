from rest_framework import serializers


def _translation_value(obj, language, attr):
    translations = list(obj.translations.all())
    row = next((t for t in translations if t.language == language), None)
    row = row or (translations[0] if translations else None)
    return getattr(row, attr, "") if row else ""


class PostSummarySerializer(serializers.Serializer):
    """Summarized blog post entry for card grids and preview listings."""

    id = serializers.IntegerField()
    slug = serializers.CharField()
    author = serializers.CharField()
    banner_image = serializers.SerializerMethodField()
    published_at = serializers.DateTimeField()
    title_es = serializers.SerializerMethodField()
    title_en = serializers.SerializerMethodField()
    description_es = serializers.SerializerMethodField()
    description_en = serializers.SerializerMethodField()
    keywords_es = serializers.SerializerMethodField()
    keywords_en = serializers.SerializerMethodField()
    sort_order = serializers.IntegerField()

    def get_banner_image(self, obj):
        return obj.banner_image.url if obj.banner_image else None

    def get_title_es(self, obj):
        return _translation_value(obj, "es", "title")

    def get_title_en(self, obj):
        return _translation_value(obj, "en", "title")

    def get_description_es(self, obj):
        return _translation_value(obj, "es", "description")

    def get_description_en(self, obj):
        return _translation_value(obj, "en", "description")

    def get_keywords_es(self, obj):
        return _translation_value(obj, "es", "keywords")

    def get_keywords_en(self, obj):
        return _translation_value(obj, "en", "keywords")


class PostDetailSerializer(PostSummarySerializer):
    """Detailed blog post entry including full bilingual markdown content."""

    content_es = serializers.SerializerMethodField()
    content_en = serializers.SerializerMethodField()

    def get_content_es(self, obj):
        return _translation_value(obj, "es", "content")

    def get_content_en(self, obj):
        return _translation_value(obj, "en", "content")
