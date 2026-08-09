## Context

`artworks/admin.py` defines 10 translation inlines (`ArtistTranslationInline`, `ArtCuratorTranslationInline`, `DisciplineTranslationInline`, `TechniqueTranslationInline`, `ThemeTranslationInline`, `FormatTranslationInline`, `ScaleTranslationInline`, `GalleryTranslationInline`, `LocationTranslationInline`, `ArtworkTranslationInline`). Each is a `unfold.admin.StackedInline` that shares:

- `TranslationInlineFormSet` (pre-fills `language` on extra forms from the missing languages)
- `verbose_name = "Traducción"`, `verbose_name_plural = "Traducciones (Español / Inglés)"`
- `max_num = len(settings.LANGUAGES)` and an identical `get_extra` returning `max(0, len(settings.LANGUAGES) - existing_count)`

`settings.LANGUAGES = [("es", "Español"), ("en", "English")]` (settings.py:119). All translation models extend `TranslationBase` (core/models.py:25) with `unique_together = (parent_fk, "language")`. Every parent's FK uses the same related name `translations`.

What is missing: no way to delete a row (currently possible), and no guarantee both languages are filled (a blank row is dropped on save, and for the bio-only inlines an untouched inline is skipped entirely because the extra forms are unchanged). django-unfold 0.77.1 (pinned in requirements.txt) inlines inherit from Django's `InlineModelAdmin`, so standard attributes (`can_delete`, `min_num`, `max_num`) work unchanged.

## Goals / Non-Goals

**Goals:**
- A single shared base inline class carrying all common translation-inline behavior.
- Exactly two translation rows per parent, always (`es` + `en`), enforced on save including legacy data.
- No per-row delete control in any translation inline.

**Non-Goals:**
- No data migration or backfill script — incomplete legacy rows surface as validation errors and must be completed by the editor (per decision "Enforce on all rows, even legacy").
- No model/database changes, no new dependencies, no API or frontend changes.
- Not touching `ArtworkImageInline` (has `alt_es`/`alt_en` columns but is not a translation inline).

## Decisions

### D1: One shared base class `TranslationInline(StackedInline)`
All 10 inlines subclass it, defining only `model` and `fields`. The base carries `formset = TranslationInlineFormSet`, `can_delete = False`, `min_num = max_num = len(settings.LANGUAGES)`, verbose names, and the existing `get_extra`.

Rationale: the inlines are byte-for-byte identical except `model`/`fields`; one shared class removes ~40 duplicated lines and centralizes the enforcement. Alternative considered: a mixin — rejected, a base class is the simpler inheritance relationship since every class is always a translation inline.

### D2: Enforce "exactly two" with a `clean()` override on the formset, `max_num`, and `can_delete = False`
- `max_num = len(settings.LANGUAGES)` caps the number of rows (already present).
- `can_delete = False` removes the per-row delete checkbox/trash icon (unfold renders delete controls only when `has_delete_permission`, which derives from `can_delete`).
- `validate_min = validate_max = True` on the base inline — the admin does not pass these to the formset factory (both default to `False`), so without them `min_num`/`max_num` are inert server-side. With them on, Django also raises its native "submit at least/most N forms" errors.
- A `clean()` override on `TranslationInlineFormSet` rejects the save unless exactly `len(settings.LANGUAGES)` translation rows are present, are not marked for deletion, and will actually be persisted.

`min_num`/`max_num` are complementary caps, but they are NOT the guarantee. Django's built-in `min_num` check (`total_form_count() - deleted - empty_forms_count >= min_num`) subtracts unchanged extra forms, so it does not catch a completely untouched inline: for the bio-only inlines (Artist, ArtCurator) the untouched extra forms are valid but unchanged, so they are skipped at save time (`save_new_objects` only persists changed forms), persisting zero translations. The `clean()` override closes that gap by counting the non-empty, non-deleted rows, independent of the built-in checks.

Together these satisfy the spec: no deletion, always exactly two languages, enforced on both new and legacy rows.

### D3: Extend `TranslationInlineFormSet` with a `clean()` override
The formset already pre-fills `es`/`en` on extra forms and `get_extra` already yields the missing-count of rows for existing objects; these move into the base class unchanged. Add a `clean()` that counts the non-empty, non-deleted translation rows (a row is non-empty when any translated field other than `language` is filled — the parent FK is always present in `cleaned_data`, so it is excluded too, via `self.fk.name`) and raises a `ValidationError` unless the count equals `len(settings.LANGUAGES)`.

## Risks / Trade-offs

- **Legacy parents with 0 or 1 translations block saving** until both are filled → Intended behavior (decision from user). Editors see a formset validation error, including the untouched-inline case (the `clean()` override counts the rows that would actually be persisted). If a backfill is later preferred, it can be added as a separate change.
- **Parents with more than two translation rows (dirty legacy data) become un-fixable in the UI**: `max_num` blocks the save while `can_delete = False` removes the only action that could trim a row → Today that extra row could be deleted; after this change it cannot. Escape hatch: correct the row directly in the DB or with a one-off cleanup script. Such rows should not exist via the admin (already capped at 2), but fixtures or shell writes could create them.
- **Enforcement is admin-only**: the "always two values" guarantee is not enforced at the model/DB layer, so non-admin writers (DRF API, management commands, fixtures) can still create parents with 0 or 1 translations, which then block admin editing until completed → Acceptable for this admin-scoped change; named here so the limitation is explicit.
- **Validation message wording is Django's generic "please submit at least 2 forms" text** (for `min_num`/`max_num`) or the formset `clean()` error → Acceptable; the inline title already labels rows as "Traducciones (Español / Inglés)".
- **Behavior change silently applies to all 10 inlines via the base class** → Intended (DRY). Verified by the admin test/load check in tasks: every registered admin change form loads without error.
- **`len(settings.LANGUAGES)` coupling** → Already the codebase convention (`max_num`); if a third language is added later, inlines automatically support it and `clean()` follows.

## Migration Plan

- Implementation is admin-only and reversible: revert the diff in `artworks/admin.py`. No data migration required.
- No rollout steps beyond deploying the code; the enforcement applies immediately to all admin change forms.
