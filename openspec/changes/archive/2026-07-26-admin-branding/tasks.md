## 1. Update UNFOLD sidebar settings in project/settings.py

- [x] 1.1 Change `SITE_HEADER` from `"Enredarte"` to `"ENREDARTE DASHBOARD"`
- [x] 1.2 Change `SITE_SUBHEADER` from `"Panel de Administracion"` to `"Sistema de gestión"`
- [x] 1.3 Remove the `SITE_LOGO` line from the UNFOLD dict

## 2. Update primary color palette in project/settings.py

- [x] 2.1 Replace `COLORS.primary` values with the red palette (hue 20°, anchored at `#c41e3a`):

| Level | Value |
|-------|-------|
| 50 | `oklch(0.97 0.02 20)` |
| 100 | `oklch(0.92 0.04 20)` |
| 200 | `oklch(0.85 0.08 20)` |
| 300 | `oklch(0.75 0.12 20)` |
| 400 | `oklch(0.64 0.17 20)` |
| 500 | `oklch(0.53 0.20 20)` |
| 600 | `oklch(0.44 0.18 20)` |
| 700 | `oklch(0.36 0.15 20)` |
| 800 | `oklch(0.29 0.12 20)` |
| 900 | `oklch(0.22 0.08 20)` |
| 950 | `oklch(0.17 0.04 20)` |

## 3. Verify

- [x] 3.1 Start the dev server and confirm the sidebar shows the icon with "ENREDARTE DASHBOARD" and "Sistema de gestión" text
- [x] 3.2 Confirm primary-colored elements (buttons, links, focus rings) render in red tones
- [x] 3.3 Check WCAG contrast on primary-600 buttons against white text
