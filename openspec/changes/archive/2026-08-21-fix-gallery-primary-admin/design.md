## Context

`Gallery.is_primary` (added in commit `6e4bb6c`) identifies the single main gallery. Uniqueness is enforced two ways:

1. `Gallery.save()` unflags any other primary gallery before saving (`artworks/models.py:150`).
2. A DB-level conditional unique constraint `unique_primary_gallery` rejects a second primary for writes that bypass the ORM override.

The bug: Django's `ModelForm.full_clean()` runs `validate_constraints()` **before** `save()`. When a second primary gallery already exists in the DB and the admin user toggles `is_primary=True` on another gallery, constraint validation fails with `No se cumple la restricción "unique_primary_gallery"`. `save()` — the only place that unflags the previous primary — never runs. The reported behavior (form should accept the change and unflag the old primary) requires unflagging to happen **before** the constraint is validated.

Reproduced by driving the real admin model form against the running DB:

```
form valid: False
form errors: {"__all__": [{"message": "No se cumple la restricción \"unique_primary_gallery\""}]}
A.primary = True | B.primary = False   # nothing was unmarked
```

## Goals / Non-Goals

**Goals:**

- Submitting `is_primary=True` from the admin change/add form succeeds while the previous primary is unmarked.
- Keep the DB constraint as the backstop for non-ORM writes.
- Cover the fix with a regression test that exercises the admin form path (the actual reported failure).

**Non-Goals:**

- Removing or relaxing the `unique_primary_gallery` DB constraint.
- Changing `Gallery.save()` behavior for plain ORM writes — those already work.
- Any API serializer or migration changes.
- A generic reusable "single active flag" form mixin for the whole codebase (out of scope; only `Gallery.is_primary` is affected today).

## Decisions

### Decision: Admin-level `clean()` unflags the previous primary before validation

A `GalleryAdminForm(forms.ModelForm)` with:

```python
def clean(self):
    cleaned = super().clean()
    if cleaned.get("is_primary", False):
        Gallery.objects.filter(is_primary=True).exclude(pk=self.instance.pk).update(is_primary=False)
    return cleaned
```

Wired into `GalleryAdmin` via `form = GalleryAdminForm`.

**Rationale:** `clean()` runs during `full_clean()`, before `validate_constraints()`, so the previous primary is gone by the time the unique constraint is checked. It is the standard Django mechanism for cross-field/cross-instance validation on `ModelForm`s. The `.update()` avoids recursive saves.

- Existing gallery (`instance.pk` set): excludes itself, so a gallery re-saving itself as primary doesn't self-destruct.
- New gallery (`instance.pk is None`): nothing excluded → any existing primary is unmarked.

**Alternatives considered:**

1. **Put the unflag in `Gallery.clean()` on the model** — covers every form path automatically. Rejected: it performs a DB write inside `full_clean()` for every caller of `is_valid()`, including unrelated contexts, and data + behavior already exist in `save()`; keeping the admin-specific concern in the admin layer is more targeted and avoids surprising non-admin `full_clean()` callers with side-effecting writes during validation.
2. **Override `save_model()` on `GalleryAdmin`** — runs too late: the form is already validated by then, so the constraint error would still surface before `save_model()` is reached.
3. **Remove the DB constraint and rely solely on `save()`** — rejected: loses the backstop for `bulk_create()` (there is an existing test asserting `IntegrityError` for that path), fixtures, and raw SQL.

### Decision: Keep `Gallery.save()` unchanged

The existing unflag-on-save remains the mechanism for plain ORM writes. With the admin form fix, all three paths converge:

| Write path | Unflag mechanism | Constraint check |
|---|---|---|
| Admin form | `GalleryAdminForm.clean()` | passes (previous primary already cleared) |
| ORM `save()`/`create()` | `Gallery.save()` override | passes |
| `bulk_create()` / raw SQL | none (intentional) | DB constraint rejects |

### Decision: Synchronize the archive spec into `openspec/specs/gallery-primary-flag/spec.md`

The archived change `2026-08-18-add-gallery-is-primary` already synced `gallery-primary-flag` specs. This change updates the "Only one primary gallery exists" requirement to cover form-based saves and adds the admin-form scenario. Per project convention, after implementation the delta spec is synced into `openspec/specs/`.

## Risks / Trade-offs

- [The admin `clean()` performs a write during form validation; if a later `clean()`/per-field validation fails, unflagging already happened but the save is rolled back] → The unflag happens inside `transaction.atomic` already wrapped by admin save flows; if the form ultimately rejects, the admin transaction does not commit (no `save()` was called), so the DB is not persisted. Field-level validation has already run before `clean()`.
- [A user unchecks `is_primary` on the currently-primary gallery, leaving zero primaries] → Accepted behavior, unchanged from today (constraint only forbids `>1` primary, not `0`). Not addressed by this change.
- [Concurrent edits: two admins each flag a different gallery simultaneously] → The write-then-validate ordering means one may still hit `unique_primary_gallery` on rare races; that surfaces as a form error, which is the correct backstop behavior. Not resolved here.

## Migration Plan

No schema or data migration. Deploy as part of the normal release: `openspec-apply` implements the form, the regression test runs in CI, and the delta spec is synced after archive. Rollback: revert the admin form code; the DB constraint and `save()` override are unchanged.

## Open Questions

None.