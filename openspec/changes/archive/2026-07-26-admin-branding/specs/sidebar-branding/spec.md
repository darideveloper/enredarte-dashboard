## ADDED Requirements

### Requirement: Sidebar shows icon with header and subheader text
The admin sidebar header SHALL display the site icon alongside the site header and subheader text when no `SITE_LOGO` is configured.

#### Scenario: Sidebar header renders icon + text
- **WHEN** the admin page loads
- **THEN** the sidebar header shows `SITE_ICON` image, `SITE_HEADER` text "ENREDARTE DASHBOARD", and `SITE_SUBHEADER` text "Sistema de gestión"

### Requirement: Primary color palette uses brand red
The admin UI SHALL use a red primary color palette anchored at `#c41e3a` as the primary-500 value, replacing the previous purple palette.

#### Scenario: Primary color is red
- **WHEN** any primary-colored element renders (button, link, focus ring, active state)
- **THEN** the color SHALL be derived from the red palette at hue 20° with `oklch(0.53 0.20 20)` as the 500 value
