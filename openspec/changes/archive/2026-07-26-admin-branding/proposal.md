## Why

The admin sidebar currently uses `SITE_LOGO` which replaces both `SITE_HEADER` and `SITE_SUBHEADER` text, hiding the site title and subtitle. Additionally, the primary color (purple, hue 296°) doesn't match the brand identity. Updating both the sidebar header layout and the color scheme creates a cohesive brand experience.

## What Changes

- Remove `SITE_LOGO` from `UNFOLD` settings in `project/settings.py`
- Rename `SITE_HEADER` from `"Enredarte"` to `"ENREDARTE DASHBOARD"`
- Rename `SITE_SUBHEADER` from `"Panel de Administracion"` to `"Sistema de gestión"`
- Replace primary color palette (purple, hue 296°) with a red palette anchored at `#c41e3a` (hue 20°)
- `SITE_ICON` remains unchanged (continues to render the favicon logo next to header text)

## Capabilities

### New Capabilities
*(None — this is a configuration-only change.)*

### Modified Capabilities
*(No spec-level behavior changes.)*

## Impact

- **`project/settings.py`**: Remove 1 line (`SITE_LOGO`), update 2 values (`SITE_HEADER`, `SITE_SUBHEADER`), replace 11 values in `COLORS.primary`
- **Sidebar rendering**: `SITE_LOGO` removal causes Unfold to fall through to the `SITE_ICON` + `branding` branch in `navigation_header.html`, showing the icon plus header/subheader text
- **UI theme**: All primary-colored elements (buttons, links, focus rings, active states) shift from purple to red
