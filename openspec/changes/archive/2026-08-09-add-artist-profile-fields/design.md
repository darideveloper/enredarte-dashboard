## Context

The `Artist` model today carries only `name/email/website/photo/birth_year/death_year` plus a translatable `bio` (`artworks/models.py:6-16`). `Artwork` carries five taxonomy M2M axes, prices, `status`, images, and gallery links. There is no public API yet (empty DRF router), and the admin is the only consumer.

The client's artist profile page has ten blocks. Three are already backed by data (bio, taxonomy data, artworks), one is deferred ("más vendidos"), and the rest need either new model fields or a reusable computation. The taxonomy work (`align-artwork-taxonomies`) already landed and provides `Technique` and the `artworks` reverse relations that the derived blocks build on.

## Goals / Non-Goals

**Goals:**
- Add the missing data layer: `ArtistSocialLink`, `Location` (+ translations), `Artwork.is_highlighted`, `Artwork.views_count`.
- Provide the six derived profile blocks as reusable model properties on `Artist` (`techniques`, `available_artworks`, `new_additions`, `highlighted_artworks`, `most_viewed`, `curations`).
- Surface everything in the admin (form fields, inline, readonly "Resumen" fieldset, changelist/filters) so an editor can capture and see all profile data.
- Keep the computed blocks in ONE place so the future DRF API and the admin share them.

**Non-Goals:**
- No public API/serializers — the properties are the contract the future API will consume.
- No view-tracking increments (there are no views; `views_count` is admin-editable until then).
- No "más vendidos" modeling (depends on the future sales app).
- No changes to the existing `ArtistTranslation.bio` (already done).

## Decisions

### 1. Derived blocks are model properties returning QuerySets
Each derived block is a `@property` on `Artist` returning a lazy QuerySet. The admin "Resumen" fieldset renders them via `display_*` methods; future DRF serializers call the same properties (`SerializerMethodField`). No computation is duplicated anywhere.

- `techniques` → `Technique.objects.filter(artworks__artist=self).distinct().order_by("sort_order")`
- `available_artworks` → `self.artworks.filter(is_active=True, status=ArtworkStatus.AVAILABLE).order_by("sort_order")`
- `new_additions` → `self.artworks.filter(is_active=True).order_by("-created_at")`
- `highlighted_artworks` → `self.artworks.filter(is_active=True, is_highlighted=True).order_by("sort_order")`
- `most_viewed` → `self.artworks.filter(is_active=True).order_by("-views_count")`
- `curations` → `Gallery.objects.filter(artwork_links__artwork__artist=self, is_active=True).distinct()`

Despite the client-facing label "Curadurías", the block means *galleries exhibiting the artist's works* (confirmed with the user), so `curations` returns `Gallery` objects — NOT `ArtCurator`s. Each property carries a docstring stating what it returns and which profile block it backs, so the future DRF serializer and admin methods interpret them the same way.

**Alternative considered:** compute in admin + separately in future serializers. Rejected — the user explicitly wants the calculations reusable by admin and DRF.

### 2. `ArtistSocialLink` extends `BaseModel`, like the existing FK-detail models
`ArtworkImage` and `ArtworkGallery` already extend `BaseModel` (slug, is_active, sort_order, timestamps). `ArtistSocialLink` follows the same pattern: `artist` FK (`related_name="social_links"`), `platform` as `TextChoices` (Instagram, Facebook, X, TikTok, LinkedIn, YouTube, Behance, Other), `url`, `sort_order`, `Meta.ordering = ["sort_order"]`.

`BaseModel.slug` is `unique` with no default; inline forms exclude it (same as `ArtworkImageInline`), so `ArtistSocialLink.save()` auto-generates the slug when blank (`slugify(f"{artist.slug}-{platform}")`, appending a suffix on collision) to avoid blank-unique crashes when an artist has several links. Admin inline uses `ordering_field = "sort_order"` + `hide_ordering_field`.

**Alternative considered:** a plain `models.Model` with no slug. Rejected — inconsistent with the two existing FK-detail models and their admin inlines.

### 3. `Location` mirrors the taxonomy pattern; FK on Artist is 1:N
`Location(BaseModel)` + `LocationTranslation(TranslationBase)` with `name` and `unique_together (location, language)` — byte-for-byte the `Discipline`/`Technique` pattern. `Artist.location = FK(Location, on_delete=SET_NULL, null=True, blank=True, related_name="artists")`.

**Alternative considered:** `OneToOneField` (single location per artist). Rejected — the user confirmed one location shared by many artists (FK on Artist).

### 4. Artwork discovery fields are simple, with no ordering
`Artwork.is_highlighted = BooleanField(default=False)` (per user, no ordering needed — the artist's highlighted works derive by filtering their own artworks) and `Artwork.views_count = PositiveIntegerField(default=0)`, editable in admin as a manual provisional until the public view exists to increment it.

### 5. Admin surface
- `ArtistSocialLinkInline(TabularInline)` on `ArtistAdmin` (fields `platform`, `url`, sortable).
- `LocationAdmin` + `LocationTranslationInline` mirroring the taxonomy admins (es-pref `display_name`, slug/sort init, Spanish labels "Ubicación"/"Ubicaciones").
- `ArtistAdmin` gains `location` in the form. Derived blocks are shown at two granularities from the SAME model properties: **count columns** on the changelist (`list_display` → `.count()`) and a readonly **"Resumen" fieldset** on the change form with full detail (`.all()` → names/titles/galleries). Rendering is presentation-only; properties keep returning raw QuerySets so the future DRF API serializes them natively.
- `ArtworkAdmin` exposes `is_highlighted` (form + changelist column + filter) and `views_count` (form + changelist column).

### 6. Fixtures reuse the existing loader pattern
- **Base** (`base_loaddata`): `Location.json` + `LocationTranslation.json` with 4 stable-PK locations and es/en names: 1 guadalajara, 2 jalisco, 3 occidente, 4 mexico.
- **Seed** (`seed_loaddata`): update `seed/Artist.json` to reference location PKs (e.g. artists 1–3 → 1, artist 4 → 2, artist 5 → 3); new `seed/ArtistSocialLink.json` with 2–3 demo links per seed artist.

## Risks / Trade-offs

- [Blank unique slug when several links are saved via inline] → `ArtistSocialLink.save()` auto-fills the slug from artist+platform with a uniqueness suffix.
- [Seed fixture referencing taxonomy/location PKs that drift] → PKs are fixed in fixtures and the loader is fail-soft; the manifest lives in `specs/artist-location/spec.md`.
- [N+1 queries on the admin Resumen fieldset] → trivial at catalog scale (single artist row); no prefetching added (YAGNI).
- [`views_count` won't auto-increment until the API exists] → accepted; the field is editable in admin and the contract (`order_by("-views_count")`) is already in the `most_viewed` property.

## Migration Plan

1. `python manage.py makemigrations` generates `artworks/migrations/0003_...` (3 `CreateModel` + 3 `AddField`; no data step).
2. `python manage.py migrate`.
3. `python manage.py base_loaddata` loads the 6 locations.
4. `python manage.py seed_loaddata` loads updated artists (with location) + social links.
5. Tests: `makemigrations --check`, `manage.py test`.
6. Rollback: `migrate artworks 0002` drops the new tables/columns; fixtures remain for re-seed.

## Open Questions

None blocking — all decisions (scope, curadurías meaning, social link model, location shape/relation, highlighted flag, views counter, "más vendidos" deferral, admin presentation) were confirmed with the user.
