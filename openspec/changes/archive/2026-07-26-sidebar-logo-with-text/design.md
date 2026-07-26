## Context

The admin sidebar is rendered by Unfold's `navigation_header.html`, which uses an if/elif chain: if `SITE_LOGO` is set, only the logo image renders (no text); elif `branding` is set, the icon + `SITE_HEADER` + `SITE_SUBHEADER` render. Currently `SITE_LOGO` is set, so header/subheader text is hidden.

## Goals / Non-Goals

**Goals:**
- Show the logo image alongside "ENREDARTE DASHBOARD" and "Sistema de gestión" text in the sidebar header
- Simple configuration-only change — no template overrides needed

**Non-Goals:**
- No CSS, JS, or template changes
- No new dependencies

## Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Approach | Remove `SITE_LOGO`, keep `SITE_ICON` | Unfold 0.97.0 renders `SITE_ICON` + branding text when `SITE_LOGO` is absent. Minimal change — 1 line removed, 2 values updated. |
| Header text | `"ENREDARTE DASHBOARD"` | Clear site identity in the sidebar |
| Subheader text | `"Sistema de gestión"` | Describes the admin purpose |

## Risks / Trade-offs

- **Logo size**: The icon renders at `h-[38px]` (from `site_icon.html`), smaller than the `h-8` logo. If the current `logo.webp` contains branding details that look bad at 38px, the existing `favicon.png` is already the correct asset for this size. Swap the asset only if needed.
