from django.db import models

from core.models import BaseModel, Person, TranslationBase


class Artist(Person):
    birth_year = models.IntegerField(null=True, blank=True)
    death_year = models.IntegerField(null=True, blank=True)


class ArtistTranslation(TranslationBase):
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE, related_name="translations")
    bio = models.TextField(blank=True)

    class Meta:
        unique_together = [("artist", "language")]


class ArtCurator(Person):
    pass


class ArtCuratorTranslation(TranslationBase):
    art_curator = models.ForeignKey(ArtCurator, on_delete=models.CASCADE, related_name="translations")
    bio = models.TextField(blank=True)

    class Meta:
        unique_together = [("art_curator", "language")]


class Gallery(BaseModel):
    logo = models.ImageField(null=True, blank=True)
    curator = models.ForeignKey(
        ArtCurator, on_delete=models.SET_NULL, null=True, blank=True, related_name="curated_galleries"
    )


class GalleryTranslation(TranslationBase):
    gallery = models.ForeignKey(Gallery, on_delete=models.CASCADE, related_name="translations")
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    class Meta:
        unique_together = [("gallery", "language")]


class Discipline(BaseModel):
    class Meta:
        verbose_name = "Disciplina"
        verbose_name_plural = "Disciplinas"


class DisciplineTranslation(TranslationBase):
    discipline = models.ForeignKey(Discipline, on_delete=models.CASCADE, related_name="translations")
    name = models.CharField(max_length=200)

    class Meta:
        unique_together = [("discipline", "language")]


class Technique(BaseModel):
    class Meta:
        verbose_name = "Técnica"
        verbose_name_plural = "Técnicas"


class TechniqueTranslation(TranslationBase):
    technique = models.ForeignKey(Technique, on_delete=models.CASCADE, related_name="translations")
    name = models.CharField(max_length=200)

    class Meta:
        unique_together = [("technique", "language")]


class Theme(BaseModel):
    class Meta:
        verbose_name = "Temática"
        verbose_name_plural = "Temáticas"


class ThemeTranslation(TranslationBase):
    theme = models.ForeignKey(Theme, on_delete=models.CASCADE, related_name="translations")
    name = models.CharField(max_length=200)

    class Meta:
        unique_together = [("theme", "language")]


class Format(BaseModel):
    class Meta:
        verbose_name = "Tipo de pieza"
        verbose_name_plural = "Tipos de pieza"


class FormatTranslation(TranslationBase):
    format = models.ForeignKey(Format, on_delete=models.CASCADE, related_name="translations")
    name = models.CharField(max_length=200)

    class Meta:
        unique_together = [("format", "language")]


class Scale(BaseModel):
    class Meta:
        verbose_name = "Tamaño"
        verbose_name_plural = "Tamaños"


class ScaleTranslation(TranslationBase):
    scale = models.ForeignKey(Scale, on_delete=models.CASCADE, related_name="translations")
    name = models.CharField(max_length=200)

    class Meta:
        unique_together = [("scale", "language")]


class ArtworkStatus(models.TextChoices):
    AVAILABLE = "available", "Available"
    SOLD = "sold", "Sold"
    RESERVED = "reserved", "Reserved"
    ON_LOAN = "on_loan", "On Loan"
    NOT_AVAILABLE = "not_available", "Not Available"


class Artwork(BaseModel):
    artist = models.ForeignKey(Artist, on_delete=models.PROTECT, related_name="artworks")
    year = models.IntegerField()
    dimensions = models.CharField(max_length=100)
    disciplines = models.ManyToManyField(Discipline, related_name="artworks", blank=True)
    techniques = models.ManyToManyField(Technique, related_name="artworks", blank=True)
    themes = models.ManyToManyField(Theme, related_name="artworks", blank=True)
    formats = models.ManyToManyField(Format, related_name="artworks", blank=True)
    scales = models.ManyToManyField(Scale, related_name="artworks", blank=True)
    price_mxn = models.DecimalField(max_digits=10, decimal_places=2)
    price_usd = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=ArtworkStatus.choices)


class ArtworkTranslation(TranslationBase):
    artwork = models.ForeignKey(Artwork, on_delete=models.CASCADE, related_name="translations")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    class Meta:
        unique_together = [("artwork", "language")]


class ArtworkGallery(BaseModel):
    artwork = models.ForeignKey(Artwork, on_delete=models.CASCADE, related_name="gallery_links")
    gallery = models.ForeignKey(Gallery, on_delete=models.CASCADE, related_name="artwork_links")
    sort_order = models.IntegerField(default=0)

    class Meta:
        unique_together = [("artwork", "gallery")]


class ArtworkImage(BaseModel):
    artwork = models.ForeignKey(Artwork, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField()
    alt_es = models.CharField(max_length=200, blank=True)
    alt_en = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    sort_order = models.IntegerField(default=0)

    class Meta:
        ordering = ["sort_order"]
