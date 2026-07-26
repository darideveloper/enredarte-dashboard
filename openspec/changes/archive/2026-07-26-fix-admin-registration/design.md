## Context

`project/admin.py` registers custom admin classes for User, Group, and TokenProxy (from DRF authtoken). These add Unfold-specific features: `sidebar_icon`, Unfold forms (`UserChangeForm`, `UserCreationForm`, `AdminPasswordChangeForm`), `compressed_fields`, and the "Edit" action row.

The `project` package is not in `INSTALLED_APPS`, so Django's admin autodiscovery never imports `project/admin.py`. The default admin classes (with no `sidebar_icon` and no Unfold features) are used silently.

Three options were considered:

| Option | Change | Risk |
|--------|--------|------|
| **A** — `import project.admin` in `urls.py` | One line | Minimal, explicit |
| **B** — Add `"project"` to `INSTALLED_APPS` | One line | Adds `project` as an app (no models, no DB tables) — works but semantically odd |
| **C** — Move admin registrations to `artworks/admin.py` | File move + path updates | Cleaner but touches more files; `artworks` is a stub app |

**Selected: Option A** — simplest, most explicit, least side effects.

## Goals / Non-Goals

**Goals:**
- Ensure `project/admin.py` is imported at startup so custom admin classes are registered
- Restore correct `sidebar_icon` rendering for User, Group, TokenProxy
- Apply all Unfold admin customisations currently defined in `project/admin.py`

**Non-Goals:**
- No restructuring of the project layout
- No changes to admin class definitions

## Decisions

- **One-line import** in `project/urls.py`: `import project.admin` — this is the standard Django idiom for loading admin modules that aren't auto-discovered. It runs at module import time (before the URL patterns are evaluated), which is the same timing as `@admin.register` decorators.

- **Documentation note**: Add a note to personal Django docs explaining that `admin.py` in a non-app package must be explicitly imported.

## Risks / Trade-offs

- **Double registration on hot-reload**: In development with `--reload`, the import runs once per process start. No issue.
- **Doesn't fix the structural issue**: The real fix would be moving admin code into a proper app. But that's scope creep for this change.
