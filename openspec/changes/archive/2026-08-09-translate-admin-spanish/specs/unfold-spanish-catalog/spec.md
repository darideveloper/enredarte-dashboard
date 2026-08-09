## ADDED Requirements

### Requirement: Unfold-only admin strings render in Spanish
All django-unfold `{% trans %}`/`{% translate %}` msgids that are not present in Django's shipped Spanish catalog SHALL render in Spanish through a project `locale/` catalog, merging with (not replacing) Django's default catalogs.

#### Scenario: Sidebar search placeholder is Spanish
- **WHEN** the admin sidebar search input renders
- **THEN** it shows "Buscar aplicaciones y modelos…" instead of "Search apps and models..."

#### Scenario: Filter actions are Spanish
- **WHEN** the changelist filter controls render
- **THEN** they show Spanish copy for "Apply Filters", "Reset filters", "Filters", and "No data"

#### Scenario: Login and confirmation copy is Spanish
- **WHEN** the admin login and delete-confirmation pages render
- **THEN** they show Spanish copy for "Forgotten your password or username?", "Return to site", "This item will be deleted.", and "You have been successfully logged out from the administration"

#### Scenario: Empty/misc UI copy is Spanish
- **WHEN** empty states and misc controls render
- **THEN** "Nothing matched your search", "No results found", "Recent searches", "All applications", "No data", and related unfold-only strings display in Spanish

### Requirement: Catalog covers exactly the missing unfold msgids
The project catalog SHALL contain only the ~40 unfold-only msgids verified as absent from Django's `es` catalog, so base chrome (Save/Delete/pagination/login) continues to be served by Django's shipped catalogs.

#### Scenario: Django chrome is not duplicated in the project catalog
- **WHEN** the server resolves a generic admin string such as "Save" or "Delete"
- **THEN** it still resolves from Django's shipped Spanish catalog, not from the project `locale/` catalog
