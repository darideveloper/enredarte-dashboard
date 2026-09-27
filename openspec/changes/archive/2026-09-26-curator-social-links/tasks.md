## 1. Models and Migration

- [x] 1.1 In `artworks/models.py`, define abstract `BaseSocialLink(BaseModel)` containing `Platform` text choices, `platform`, `url`, `parent` abstract property, auto-slugify `save()` logic, and content-based `__str__()`. Refactor `ArtistSocialLink` to inherit from `BaseSocialLink` and verify no fields or table names change.
- [x] 1.2 In `artworks/models.py`, define `ArtCuratorSocialLink(BaseSocialLink)` with `curator = models.ForeignKey(ArtCurator, on_delete=models.CASCADE, related_name="social_links", verbose_name="Curador de arte")`, content-based `__str__()`, and `Meta` verbose names.
- [x] 1.3 Generate and apply the Django migration (`python manage.py makemigrations artworks && python manage.py migrate`) and verify the migration operation only creates `ArtCuratorSocialLink`.

## 2. Admin Inline

- [x] 2.1 In `artworks/admin.py`, implement `ArtCuratorSocialLinkInline(TabularInline)` with `fields = ["platform", "url"]`, `verbose_name = "Red social"`, `verbose_name_plural = "Redes sociales"`, and `extra = 0`.
- [x] 2.2 In `artworks/admin.py`, register `ArtCuratorSocialLinkInline` in `ArtCuratorAdmin.inlines` after `ArtCuratorTranslationInline` and verify the inline renders in the Django admin curator change view.

## 3. REST API and Serialization

- [x] 3.1 In `artworks/serializers.py`, create `ArtCuratorSocialLinkSerializer` with fields `["id", "platform", "url"]` and add `social_links = ArtCuratorSocialLinkSerializer(many=True, read_only=True)` to `ArtCuratorSerializer`.
- [x] 3.2 In `artworks/views.py`, update `ArtCuratorViewSet.get_queryset()` to prefetch active social links with `Prefetch("social_links", queryset=ArtCuratorSocialLink.objects.filter(is_active=True))`.
- [x] 3.3 Update `bruno/collections/enredarte-dashboard-api/ArtCurators/GET detail.bru` with the `social_links` field in the documentation and response payload example.

## 4. Fixtures and Seed Data

- [x] 4.1 Create `artworks/fixtures/artworks/seed/01b_ArtCuratorSocialLink.json` with 2 demo social links each for Renata Ortega (PK 1) and Hugo Salinas (PK 2).
- [x] 4.2 Run `python manage.py seed_loaddata` and verify the curator demo social links load cleanly without integrity errors.

## 5. Tests and Verification

- [x] 5.1 In `artworks/tests.py`, add `ArtCuratorSocialLinkModelTestCase` covering auto-generated slugs (`{curator.slug}-{platform}`), suffix collision resolution, platform choices, and `__str__` rendering.
- [x] 5.2 In `artworks/tests.py`, add admin test cases verifying `ArtCuratorSocialLinkInline` is in `ArtCuratorAdmin.inlines` and change forms save with and without social links.
- [x] 5.3 In `artworks/tests.py`, add API test cases verifying `GET /api/artworks/art-curators/{id}/` returns active social links and excludes inactive (`is_active=False`) links.
- [x] 5.4 Run the test suite with `venv/bin/python manage.py test artworks.tests` and verify all tests pass.
