## ADDED Requirements

### Requirement: Sidebar shows icon with header and subheader text
The admin sidebar header SHALL display the site icon alongside the site header and subheader text when no `SITE_LOGO` is configured.

#### Scenario: Sidebar header renders icon + text
- **WHEN** the admin page loads
- **THEN** the sidebar header shows `SITE_ICON` image, `SITE_HEADER` text "ENREDARTE DASHBOARD", and `SITE_SUBHEADER` text "Sistema de gestión"
