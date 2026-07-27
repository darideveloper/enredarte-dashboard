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


class Category(BaseModel):
    pass


class CategoryTranslation(TranslationBase):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="translations")
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    class Meta:
        unique_together = [("category", "language")]


class Medium(BaseModel):
    pass


class MediumTranslation(TranslationBase):
    medium = models.ForeignKey(Medium, on_delete=models.CASCADE, related_name="translations")
    name = models.CharField(max_length=200)

    class Meta:
        unique_together = [("medium", "language")]


class Surface(BaseModel):
    pass


class SurfaceTranslation(TranslationBase):
    surface = models.ForeignKey(Surface, on_delete=models.CASCADE, related_name="translations")
    name = models.CharField(max_length=200)

    class Meta:
        unique_together = [("surface", "language")]


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
    medium = models.ForeignKey(Medium, on_delete=models.PROTECT, related_name="artworks")
    surface = models.ForeignKey(Surface, on_delete=models.PROTECT, related_name="artworks")
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="artworks")
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
