from django.conf import settings
from django.db import models
from django.utils.text import slugify


def unique_slugify(base, queryset):
    """Return a slugified, queryset-unique slug (appending -1, -2, ... on collision)."""
    base_slug = slugify(base)[:200]
    slug = base_slug
    counter = 1
    while queryset.filter(slug=slug).exists():
        suffix = f"-{counter}"
        slug = f"{base_slug[: max(1, 200 - len(suffix))]}{suffix}"
        counter += 1
    return slug


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creado el", db_index=True)
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Actualizado el")

    class Meta:
        abstract = True


class BaseModel(TimeStampedModel):
    slug = models.SlugField(max_length=200, unique=True, blank=True, verbose_name="Slug")
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    sort_order = models.IntegerField(default=0, verbose_name="Orden")

    class Meta:
        abstract = True

    def __str__(self):
        return self.slug


class TranslationBase(models.Model):
    language = models.CharField(max_length=5, choices=settings.LANGUAGES, verbose_name="Idioma")

    class Meta:
        abstract = True


class SlugBackfillMixin(models.Model):
    """Backfill the parent's slug from this translation row's ES content.

    Applied to translation models whose parent's slug is auto-generated. After
    saving an ES translation, if the parent's slug is empty it is set from
    `build_slug_base()` (default: the `slug_source` field) via `unique_slugify`.
    Non-ES translations and already-slugged parents are left untouched.
    """

    slug_source = "name"

    class Meta:
        abstract = True

    def _parent(self):
        for field in self._meta.get_fields():
            if isinstance(field, models.ForeignKey) and not field.auto_created:
                return getattr(self, field.name)
        return None

    def build_slug_base(self):
        return getattr(self, self.slug_source)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.language != "es":
            return
        parent = self._parent()
        if parent is None or parent.slug:
            return
        source = getattr(self, self.slug_source, None)
        if not source:
            return
        parent.slug = unique_slugify(self.build_slug_base(), type(parent)._default_manager.all())
        parent.save(update_fields=["slug"])


class TranslatableName(BaseModel):
    """Mixin for models whose display name lives in translation rows.

    Extends BaseModel so subclasses keep slug / is_active / sort_order while
    gaining the translated display lookup. `translated_name` prefers the
    Spanish translation, falls back to any available translation, and finally
    to the slug.
    """

    class Meta:
        abstract = True

    def translated_name(self, language="es"):
        t = self.translations.filter(language=language).first() or self.translations.first()
        return t.name if t else self.slug

    def __str__(self):
        return self.translated_name()


class Person(BaseModel):
    name = models.CharField(max_length=200, verbose_name="Nombre")
    email = models.EmailField(null=True, blank=True, verbose_name="Correo electrónico")
    website = models.URLField(null=True, blank=True, verbose_name="Sitio web")
    photo = models.ImageField(null=True, blank=True, verbose_name="Fotografía")

    class Meta:
        abstract = True

    def __str__(self):
        return self.name
