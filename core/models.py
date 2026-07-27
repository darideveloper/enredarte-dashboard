from django.conf import settings
from django.db import models


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class BaseModel(TimeStampedModel):
    slug = models.SlugField(max_length=200, unique=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.IntegerField(default=0)

    class Meta:
        abstract = True

    def __str__(self):
        return self.slug


class TranslationBase(models.Model):
    language = models.CharField(max_length=5, choices=settings.LANGUAGES)

    class Meta:
        abstract = True


class Person(BaseModel):
    name = models.CharField(max_length=200)
    email = models.EmailField(null=True, blank=True)
    website = models.URLField(null=True, blank=True)
    photo = models.ImageField(null=True, blank=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.name
