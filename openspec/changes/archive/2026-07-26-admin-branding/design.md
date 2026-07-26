## Context

The admin sidebar is rendered by Unfold's `navigation_header.html`, which uses an if/elif chain: if `SITE_LOGO` is set, only the logo image renders (no text); elif `branding` is set, the icon + `SITE_HEADER` + `SITE_SUBHEADER` render. Currently `SITE_LOGO` is set, so header/subheader text is hidden.

The primary color palette uses purple (hue 296°). The brand color is red `#c41e3a`.

## Goals / Non-Goals

**Goals:**
- Show the logo image alongside "ENREDARTE DASHBOARD" and "Sistema de gestión" text in the sidebar header
- Change the primary color from purple to red, with `#c41e3a` as the exact primary-500 value
- Configuration-only change — no template overrides needed

**Non-Goals:**
- No CSS, JS, or template changes
- No new dependencies
- No changes to the `base` color palette (grays/borders/backgrounds)

## Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Sidebar approach | Remove `SITE_LOGO`, keep `SITE_ICON` | Unfold 0.97.0 renders `SITE_ICON` + branding text when `SITE_LOGO` is absent. Minimal change. |
| Header text | `"ENREDARTE DASHBOARD"` | Clear site identity in the sidebar |
| Subheader text | `"Sistema de gestión"` | Describes the admin purpose |
| Color approach | Anchored palette around `#c41e3a` | Brand color is exactly primary-500, full scale derived from it |
| Palette generation | Manual OKLCH interpolation | OKLCH hue stays constant at 20°, lightness and chroma vary per stop. `#c41e3a` = `oklch(0.53 0.20 20)` |

## Risks / Trade-offs

- **Logo size**: The icon renders at `h-[38px]` (from `site_icon.html`), smaller than the `h-8` logo. Swap the asset only if the current `logo.webp` looks bad at 38px.
- **Color contrast**: Red primary-600 (`oklch(0.44 0.18 20)`) against white text has lower contrast than the current purple. Verify WCAG AA compliance (4.5:1) on buttons and links.
- **Compressed light end**: Because `#c41e3a` is fairly dark for a 500 (L=0.53 vs typical ~0.63), the lighter shades (50-400) have less room to graduate. This is a natural consequence of having a darker brand color.
