from django.db import models
from django.utils.text import slugify

from core.models import BaseModel, Person, TranslatableName, TranslationBase


class Artist(Person):
    birth_year = models.IntegerField(null=True, blank=True, verbose_name="Año de nacimiento")
    death_year = models.IntegerField(null=True, blank=True, verbose_name="Año de fallecimiento")
    location = models.ForeignKey(
        "Location", on_delete=models.SET_NULL, null=True, blank=True, related_name="artists",
        verbose_name="Ubicación",
    )

    class Meta:
        verbose_name = "Artista"
        verbose_name_plural = "Artistas"

    @property
    def techniques(self):
        """Distinct Technique across the artist's artworks (profile "Técnicas" block)."""
        return Technique.objects.filter(artworks__artist=self).distinct().order_by("sort_order")

    @property
    def available_artworks(self):
        """Active artworks with status available (profile "Obras disponibles" block)."""
        return self.artworks.filter(
            is_active=True, status=ArtworkStatus.AVAILABLE
        ).order_by("sort_order")

    @property
    def new_additions(self):
        """Active artworks, newest first (profile "Nuevas incorporaciones" block)."""
        return self.artworks.filter(is_active=True).order_by("-created_at")

    @property
    def highlighted_artworks(self):
        """Active featured artworks (profile "Destacados" block)."""
        return self.artworks.filter(is_active=True, is_highlighted=True).order_by("sort_order")

    @property
    def most_viewed(self):
        """Active artworks by views, most first (profile "Más visitados" block)."""
        return self.artworks.filter(is_active=True).order_by("-views_count")

    @property
    def curations(self):
        """Distinct active Gallery objects exhibiting the artist's works (profile "Curadurías" block)."""
        return Gallery.objects.filter(
            artwork_links__artwork__artist=self, is_active=True
        ).distinct()


class ArtistTranslation(TranslationBase):
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE, related_name="translations", verbose_name="Artista")
    bio = models.TextField(blank=True, verbose_name="Biografía")

    class Meta:
        unique_together = [("artist", "language")]

    def __str__(self):
        return f"{self.artist} ({self.language})"


class ArtistSocialLink(BaseModel):
    class Platform(models.TextChoices):
        INSTAGRAM = "instagram", "Instagram"
        FACEBOOK = "facebook", "Facebook"
        X = "x", "X (Twitter)"
        TIKTOK = "tiktok", "TikTok"
        LINKEDIN = "linkedin", "LinkedIn"
        YOUTUBE = "youtube", "YouTube"
        BEHANCE = "behance", "Behance"
        OTHER = "other", "Otra"

    artist = models.ForeignKey(Artist, on_delete=models.CASCADE, related_name="social_links", verbose_name="Artista")
    platform = models.CharField(max_length=20, choices=Platform.choices, verbose_name="Plataforma")
    url = models.URLField(verbose_name="URL")

    class Meta:
        ordering = ["sort_order"]

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(f"{self.artist.slug}-{self.platform}")
            slug = base
            counter = 1
            while ArtistSocialLink.objects.filter(slug=slug).exists():
                slug = f"{base}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_platform_display()} — {self.artist}"


class Location(TranslatableName):
    class Meta:
        verbose_name = "Ubicación"
        verbose_name_plural = "Ubicaciones"


class LocationTranslation(TranslationBase):
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name="translations", verbose_name="Ubicación")
    name = models.CharField(max_length=200, verbose_name="Nombre")

    class Meta:
        unique_together = [("location", "language")]

    def __str__(self):
        return f"{self.location} ({self.language})"


class ArtCurator(Person):
    class Meta:
        verbose_name = "Curador de arte"
        verbose_name_plural = "Curadores de arte"


class ArtCuratorTranslation(TranslationBase):
    art_curator = models.ForeignKey(ArtCurator, on_delete=models.CASCADE, related_name="translations", verbose_name="Curador de arte")
    bio = models.TextField(blank=True, verbose_name="Biografía")

    class Meta:
        unique_together = [("art_curator", "language")]

    def __str__(self):
        return f"{self.art_curator} ({self.language})"


class Gallery(TranslatableName):
    logo = models.ImageField(null=True, blank=True, verbose_name="Logotipo")
    curator = models.ForeignKey(
        ArtCurator, on_delete=models.SET_NULL, null=True, blank=True, related_name="curated_galleries",
        verbose_name="Curador",
    )

    class Meta:
        verbose_name = "Galería"
        verbose_name_plural = "Galerías"


class GalleryTranslation(TranslationBase):
    gallery = models.ForeignKey(Gallery, on_delete=models.CASCADE, related_name="translations", verbose_name="Galería")
    name = models.CharField(max_length=200, verbose_name="Nombre")
    description = models.TextField(blank=True, verbose_name="Descripción")

    class Meta:
        unique_together = [("gallery", "language")]

    def __str__(self):
        return f"{self.gallery} ({self.language})"


class Discipline(TranslatableName):
    class Meta:
        verbose_name = "Disciplina"
        verbose_name_plural = "Disciplinas"


class DisciplineTranslation(TranslationBase):
    discipline = models.ForeignKey(Discipline, on_delete=models.CASCADE, related_name="translations", verbose_name="Disciplina")
    name = models.CharField(max_length=200, verbose_name="Nombre")

    class Meta:
        unique_together = [("discipline", "language")]

    def __str__(self):
        return f"{self.discipline} ({self.language})"


class Technique(TranslatableName):
    class Meta:
        verbose_name = "Técnica"
        verbose_name_plural = "Técnicas"


class TechniqueTranslation(TranslationBase):
    technique = models.ForeignKey(Technique, on_delete=models.CASCADE, related_name="translations", verbose_name="Técnica")
    name = models.CharField(max_length=200, verbose_name="Nombre")

    class Meta:
        unique_together = [("technique", "language")]

    def __str__(self):
        return f"{self.technique} ({self.language})"


class Theme(TranslatableName):
    class Meta:
        verbose_name = "Temática"
        verbose_name_plural = "Temáticas"


class ThemeTranslation(TranslationBase):
    theme = models.ForeignKey(Theme, on_delete=models.CASCADE, related_name="translations", verbose_name="Temática")
    name = models.CharField(max_length=200, verbose_name="Nombre")

    class Meta:
        unique_together = [("theme", "language")]

    def __str__(self):
        return f"{self.theme} ({self.language})"


class Format(TranslatableName):
    class Meta:
        verbose_name = "Tipo de pieza"
        verbose_name_plural = "Tipos de pieza"


class FormatTranslation(TranslationBase):
    format = models.ForeignKey(Format, on_delete=models.CASCADE, related_name="translations", verbose_name="Tipo de pieza")
    name = models.CharField(max_length=200, verbose_name="Nombre")

    class Meta:
        unique_together = [("format", "language")]

    def __str__(self):
        return f"{self.format} ({self.language})"


class Scale(TranslatableName):
    class Meta:
        verbose_name = "Tamaño"
        verbose_name_plural = "Tamaños"


class ScaleTranslation(TranslationBase):
    scale = models.ForeignKey(Scale, on_delete=models.CASCADE, related_name="translations", verbose_name="Tamaño")
    name = models.CharField(max_length=200, verbose_name="Nombre")

    class Meta:
        unique_together = [("scale", "language")]

    def __str__(self):
        return f"{self.scale} ({self.language})"


class ArtworkStatus(models.TextChoices):
    AVAILABLE = "available", "Disponible"
    SOLD = "sold", "Vendida"
    RESERVED = "reserved", "Reservada"
    ON_LOAN = "on_loan", "En préstamo"
    NOT_AVAILABLE = "not_available", "No disponible"


class Artwork(BaseModel):
    artist = models.ForeignKey(Artist, on_delete=models.PROTECT, related_name="artworks", verbose_name="Artista")
    year = models.IntegerField(verbose_name="Año")
    dimensions = models.CharField(max_length=100, verbose_name="Dimensiones")
    disciplines = models.ManyToManyField(Discipline, related_name="artworks", blank=True, verbose_name="Disciplinas")
    techniques = models.ManyToManyField(Technique, related_name="artworks", blank=True, verbose_name="Técnicas")
    themes = models.ManyToManyField(Theme, related_name="artworks", blank=True, verbose_name="Temáticas")
    formats = models.ManyToManyField(Format, related_name="artworks", blank=True, verbose_name="Tipos de pieza")
    scales = models.ManyToManyField(Scale, related_name="artworks", blank=True, verbose_name="Tamaños")
    price_mxn = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio (MXN)")
    price_usd = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio (USD)")
    status = models.CharField(max_length=20, choices=ArtworkStatus.choices, verbose_name="Estado")
    is_highlighted = models.BooleanField(default=False, verbose_name="Destacada")
    views_count = models.PositiveIntegerField(default=0, verbose_name="Visitas")

    class Meta:
        verbose_name = "Obra de arte"
        verbose_name_plural = "Obras de arte"

    def translated_title(self, language="es"):
        t = self.translations.filter(language=language).first() or self.translations.first()
        return t.title if t else self.slug

    def __str__(self):
        return self.translated_title()


class ArtworkTranslation(TranslationBase):
    artwork = models.ForeignKey(Artwork, on_delete=models.CASCADE, related_name="translations", verbose_name="Obra de arte")
    title = models.CharField(max_length=200, verbose_name="Título")
    description = models.TextField(blank=True, verbose_name="Descripción")

    class Meta:
        unique_together = [("artwork", "language")]

    def __str__(self):
        return f"{self.artwork} ({self.language})"


class ArtworkGallery(BaseModel):
    artwork = models.ForeignKey(Artwork, on_delete=models.CASCADE, related_name="gallery_links", verbose_name="Obra de arte")
    gallery = models.ForeignKey(Gallery, on_delete=models.CASCADE, related_name="artwork_links", verbose_name="Galería")
    sort_order = models.IntegerField(default=0, verbose_name="Orden")

    class Meta:
        unique_together = [("artwork", "gallery")]

    def __str__(self):
        return f"{self.artwork} en {self.gallery}"


class ArtworkImage(BaseModel):
    artwork = models.ForeignKey(Artwork, on_delete=models.CASCADE, related_name="images", verbose_name="Obra de arte")
    image = models.ImageField(verbose_name="Imagen")
    alt_es = models.CharField(max_length=200, blank=True, verbose_name="Texto alternativo (ES)")
    alt_en = models.CharField(max_length=200, blank=True, verbose_name="Texto alternativo (EN)")
    is_primary = models.BooleanField(default=False, verbose_name="Imagen principal")
    sort_order = models.IntegerField(default=0, verbose_name="Orden")

    class Meta:
        ordering = ["sort_order"]

    def __str__(self):
        return self.alt_es or f"Imagen de {self.artwork}"
