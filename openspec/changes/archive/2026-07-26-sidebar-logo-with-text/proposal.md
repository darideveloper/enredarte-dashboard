## Why

The admin sidebar currently uses `SITE_LOGO` which replaces both `SITE_HEADER` and `SITE_SUBHEADER` text. This hides the site title and subtitle, making navigation less informative. The branding should show the logo image alongside the site name and subtitle for clarity.

## What Changes

- Remove `SITE_LOGO` from `UNFOLD` settings in `project/settings.py`
- Rename `SITE_HEADER` from `"Enredarte"` to `"ENREDARTE DASHBOARD"`
- Rename `SITE_SUBHEADER` from `"Panel de Administracion"` to `"Sistema de gestión"`
- `SITE_ICON` remains unchanged (continues to render the favicon logo next to header text)

## Capabilities

### New Capabilities
*(None — this is a configuration-only change that modifies existing Unfold rendering.)*

### Modified Capabilities
*(No spec-level behavior changes.)*

## Impact

- **`project/settings.py`**: Remove 1 line (`SITE_LOGO`), update 2 values (`SITE_HEADER`, `SITE_SUBHEADER`)
- **Sidebar rendering**: `SITE_LOGO` removal causes Unfold to fall through to the `SITE_ICON` + `branding` branch in `navigation_header.html`, showing the icon plus header/subheader text
