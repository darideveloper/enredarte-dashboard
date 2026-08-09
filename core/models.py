from django.conf import settings
from django.db import models


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creado el", db_index=True)
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Actualizado el")

    class Meta:
        abstract = True


class BaseModel(TimeStampedModel):
    slug = models.SlugField(max_length=200, unique=True, verbose_name="Slug")
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


class Person(BaseModel):
    name = models.CharField(max_length=200, verbose_name="Nombre")
    email = models.EmailField(null=True, blank=True, verbose_name="Correo electrónico")
    website = models.URLField(null=True, blank=True, verbose_name="Sitio web")
    photo = models.ImageField(null=True, blank=True, verbose_name="Fotografía")

    class Meta:
        abstract = True

    def __str__(self):
        return self.name
