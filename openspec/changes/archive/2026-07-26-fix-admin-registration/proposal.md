## Why

`project/admin.py` registers custom Unfold-aware admin classes for User, Group, and TokenProxy models, but is never imported because `project` is not in `INSTALLED_APPS` and no module imports it. The default Django/DRF admin classes are used instead — `sidebar_icon` and all other Unfold customisations are silently ignored. Icons in the sidebar all fall back to `"database"`.

## What Changes

- Add `import project.admin` in `project/urls.py` so the custom admin classes are actually registered
- Document the pattern in personal Django notes at `/home/daridev/Desktop/obsidian/daridev/20-areas/work/django`

## Capabilities

### New Capabilities

None. This is an operational fix with no new capability.

### Modified Capabilities

None.

## Impact

- `project/urls.py` — one-line import added
- `project/admin.py` — custom admin classes will finally execute at startup
- All model sidebar icons will now render correctly (`person`, `group`, `key`)
- Unfold customisations (`compressed_fields`, `warn_unsaved_form`, Unfold forms, etc.) will take effect
