## Context

In `artworks/admin.py`, `ArtistTranslationInline` currently sets static `extra = 2`. This causes:
1. Two unpopulated blank translation forms on new creation without defaulting one to Spanish (`es`) and the other to English (`en`).
2. Two new blank translation forms to be appended every time an existing artist with saved translations is opened for editing.

## Goals / Non-Goals

**Goals:**
- Dynamically calculate `get_extra()` based on `max(0, 2 - existing_translations_count)` so existing artists with 2 translations render zero extra blank forms.
- Set `max_num = 2` on `ArtistTranslationInline`.
- Custom inline formset or `get_formset` logic that pre-fills `language='es'` for the first translation row and `language='en'` for the second translation row (or missing languages) on creation.

**Non-Goals:**
- Modifying `artworks/models.py`.

## Decisions

### Decision 1: Dynamic `get_extra` Calculation
- **Rationale**:
  ```python
  def get_extra(self, request, obj=None, **kwargs):
      if obj:
          return max(0, 2 - obj.translations.count())
      return 2
  ```
  If `obj` has 2 translations, `get_extra` returns `0`. If `obj` has 1 translation, it returns `1`. If `obj` is new (`None`), it returns `2`.

### Decision 2: Custom Inline Formset for Language Initial Pre-population
- **Rationale**:
  Define `ArtistTranslationFormSet(BaseInlineFormSet)`:
  ```python
  class ArtistTranslationFormSet(BaseInlineFormSet):
      def __init__(self, *args, **kwargs):
          super().__init__(*args, **kwargs)
          # Pre-fill initial languages for unsaved extra forms
          existing_langs = set(self.queryset.values_list("language", flat=True)) if self.instance.pk else set()
          available_langs = [code for code, name in settings.LANGUAGES if code not in existing_langs]
          for i, form in enumerate(self.extra_forms):
              if i < len(available_langs):
                  form.initial["language"] = available_langs[i]
  ```
  This guarantees form 0 gets `es` and form 1 gets `en` automatically, and if 1 translation exists (e.g. `es`), the extra form gets `en`.

## Risks / Trade-offs

- [Risk] Custom formset logic executing on GET requests without saving. → Mitigation: `form.initial` only populates initial widget values; Django inline formset handles unsaved blank forms cleanly without creating empty rows in the DB.
