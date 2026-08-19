## Context

`Gallery` (in `artworks/models.py`) currently has `logo`, `curator`, and inherited `is_active`/timestamps. It is served read-only through `GalleryViewSet` → `GallerySerializer` at `/apis/artworks/galleries/` and managed via `GalleryAdmin`. The frontend needs a way to identify the single main gallery from the collection.

The codebase already uses boolean flags for this exact purpose:
- `Artwork.is_highlighted` ("Destacada") — exposed in serializer + admin.
- `ArtworkImage.is_primary` ("Imagen principal") — a plain boolean on a per-parent child.

We reuse the `is_primary` naming (matching `ArtworkImage`) to avoid conflating a site-wide main-gallery concept with the per-artwork "highlighted" flag.

## Goals / Non-Goals

**Goals:**
- Add `Gallery.is_primary` with a default of `False`.
- Guarantee at most one gallery is primary across the whole backend (single main gallery, active or not).
- Expose `is_primary` in the API serializer (list + detail).
- Surface `is_primary` in the Django admin (fieldset, list, filter).
- Add model + API + admin tests.

**Non-Goals:**
- No write endpoint — the API stays read-only; only admins set the flag.
- No ordering change — the galleries list keeps ordering by `-created_at`.
- No changes to `Artwork` or `ArtworkImage` flags.

## Decisions

### 1. Field name: `is_primary` (not `is_featured` / `is_highlighted`)
`ArtworkImage` already uses `is_primary`, so this keeps the vocabulary consistent across models. `is_featured` was proposed initially but is redundant with the existing "highlighted/destacada" concept used for artworks. Choosing `is_primary` avoids two similar-sounding flags with different scopes.

### 2. Single-primary uniqueness enforced at the database level
Option A semantics (one main gallery site-wide) require that the value be unique **across the whole backend**. Model-level logic alone is not enough — bulk `QuerySet.update()`, raw SQL, or direct DB edits could create a second primary. The guarantee is enforced with a **conditional unique constraint** on `is_primary` (`is_primary` is a boolean, so the constraint applies only to rows where it is `True`, allowing unlimited `False` rows).

Django 5.2 (project pins `Django>=5.2,<5.3`, PostgreSQL) supports conditional constraints, so the DB itself rejects a second primary with an `IntegrityError`:

```python
from django.db import models
from django.db.models import Q

class Meta:
    constraints = [
        models.UniqueConstraint(
            fields=["is_primary"],
            condition=Q(is_primary=True),
            name="unique_primary_gallery",
        )
    ]
```

In addition, a `save()` override keeps the UX clean (un-setting a previous primary automatically instead of surfacing a DB error):

```python
def save(self, *args, **kwargs):
    if self.is_primary:
        type(self).objects.exclude(pk=self.pk).update(is_primary=False)
    super().save(*args, **kwargs)
```

The constraint is the source of truth; the `save()` override is a convenience wrapper on top of it.

### 3. Serializer exposure
`is_primary` is a plain model field, so adding it to `GallerySerializer.Meta.fields` (next to `is_active`) auto-exposes it read-only. No `SerializerMethodField` needed.

### 4. Admin exposure
Add `is_primary` to the "Información básica" fieldset, `list_display`, and `list_filter` in `GalleryAdmin` — mirroring how `is_highlighted` is handled on `ArtworkAdmin`.

## Risks / Trade-offs

- [Second primary inserted via bulk/raw DB writes] → Rejected at the DB layer by the conditional `UniqueConstraint` (`IntegrityError`), so uniqueness holds across the whole backend regardless of how the write happens.
- [DB constraint surfaces an error instead of auto-unsetting] → The `save()` override pre-empts this for normal admin/ORM saves by un-setting the previous primary; the constraint is the safety net for everything else.
- [SQLite/other backends lack partial indexes] → The project targets PostgreSQL (`DB_ENGINE=django.db.backends.postgresql`); Django 5.2 handles the conditional constraint portably for supported backends.

## Migration Plan

1. Add field + `save()` override + `Meta.constraints` in `models.py`.
2. `python manage.py makemigrations artworks` → commit generated migration (adds the field and the conditional unique constraint).
3. `python manage.py migrate` (dev/staging) — no data backfill needed (defaults to `False`).
4. Run test suite.

Rollback: drop the migration / remove the field; existing data is unaffected since the field defaults to `False`.

## Open Questions

- None blocking. If a future need arises for per-curator main galleries, the unique constraint condition would change from global to include `curator`; the boolean field itself is unchanged.
