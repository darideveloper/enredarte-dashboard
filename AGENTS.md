# Project Conventions

## Django models — always populate admin-visible texts

Every time a Django model is created or edited, the following MUST be present
(`verbose_name`, `help_text` and `__str__` are visible in the Django Admin and
are never optional):

1. `Meta.verbose_name` and `Meta.verbose_name_plural` on every model.
2. `verbose_name` on every field.
3. `help_text` on non-obvious fields.
4. A content-based `__str__` (never Django's default `"Model object (N)"`).
5. Join / M2M-through models and translation rows also get a content-based
   `__str__`; translation rows return `"{parent} ({language})"`.

Language: **English by default**. Write Spanish literals instead if the project
follows `docs/django-i18n-es-admin.md` (Spanish Django Admin).

For translated models whose display name lives in `*Translation` rows, use the
`TranslatableName` mixin (`translated_name()` / `translated_title()`, es-first
→ any translation → slug).

Full reference: `docs/django-model-definitions.md`.
