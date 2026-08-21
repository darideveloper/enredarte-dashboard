from django.conf import settings
from django.db import models

from core.models import BaseModel, SlugBackfillMixin, TimeStampedModel, TranslationBase


class Post(BaseModel):
    banner_image = models.ImageField(
        upload_to="blog/banners",
        blank=True,
        null=True,
        verbose_name="Imagen de banner",
        help_text="Archivo de imagen de banner para la entrada",
    )
    author = models.CharField(
        max_length=200,
        default="Equipo Enredarte",
        verbose_name="Autor",
        help_text="Nombre del autor o equipo redactor",
    )
    published_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Fecha de publicación",
        help_text="Fecha y hora de publicación pública",
    )
    sort_order = models.IntegerField(
        default=0,
        verbose_name="Orden",
        help_text="Orden de la entrada dentro del listado",
    )

    class Meta:
        verbose_name = "Entrada de blog"
        verbose_name_plural = "Entradas de blog"
        ordering = ["-created_at"]

    def translated_title(self, language="es"):
        t = self.translations.filter(language=language).first() or self.translations.first()
        return t.title if t else self.slug

    def __str__(self):
        return self.translated_title()


class PostTranslation(SlugBackfillMixin, TranslationBase):
    slug_source = "title"

    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="translations",
        verbose_name="Entrada de blog",
    )
    title = models.CharField(max_length=255, verbose_name="Título")
    description = models.TextField(
        verbose_name="Descripción corta",
        help_text="Resumen o extracto de la entrada para listas y SEO",
    )
    keywords = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Palabras clave",
        help_text="Palabras clave separadas por comas",
    )
    content = models.TextField(
        verbose_name="Contenido",
        help_text="Cuerpo completo del artículo",
    )

    class Meta:
        verbose_name = "Traducción de entrada"
        verbose_name_plural = "Traducciones de entradas"
        unique_together = [("post", "language")]

    def build_slug_base(self):
        return self.title

    def __str__(self):
        return f"{self.post} ({self.language})"


class BlogImage(TimeStampedModel):
    name = models.CharField(
        max_length=255,
        verbose_name="Nombre",
        help_text="Nombre descriptivo de la imagen",
    )
    image = models.ImageField(
        upload_to="blog/images",
        verbose_name="Imagen",
        help_text="Archivo de imagen para subir",
    )

    class Meta:
        verbose_name = "Imagen de blog"
        verbose_name_plural = "Imágenes de blog"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name
