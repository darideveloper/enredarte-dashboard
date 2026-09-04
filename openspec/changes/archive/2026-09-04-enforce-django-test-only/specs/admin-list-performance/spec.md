## MODIFIED Requirements

### Requirement: Admin views render during Django tests without a staticfiles manifest
The system SHALL use Django's `IS_TESTING` (`project/settings.py:88`) to select `django.contrib.staticfiles.storage.StaticFilesStorage` for the `staticfiles` backend during `python manage.py test` (`project/settings.py:203-214`), so admin changelist, change, and add views render without requiring a `staticfiles.json` manifest built by `collectstatic`. No pytest fixture (`conftest.py`) SHALL be required. Outside tests the configured Whitenoise manifest backend SHALL remain unchanged.

#### Scenario: Django test run renders admin views
- **WHEN** the test suite runs via `python manage.py test`
- **THEN** admin changelist, change, and add views SHALL render successfully without a "Missing staticfiles manifest entry" error.

#### Scenario: Production staticfiles behavior unchanged
- **WHEN** the application runs outside tests
- **THEN** the configured `whitenoise.storage.CompressedManifestStaticFilesStorage` backend SHALL remain unchanged and SHALL still require `collectstatic` to build `staticfiles.json`.
