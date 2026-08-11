# Docs Config Coherence Specification

## Purpose
To define the requirements for consistency across the setup documentation: storage location variables, the private storage backend, Docker build ARGs, project naming, model choices style, logo filename, and the placement of Spanish-only assets must agree across `docs/` files so the docs work verbatim.

## Requirements

### Requirement: Storage location variables defined in project setup
The S3 branch in `docs/django-project-setup.md` Step 7 SHALL compute `STATIC_LOCATION`, `PUBLIC_MEDIA_LOCATION`, and `PRIVATE_MEDIA_LOCATION` from `AWS_PROJECT_FOLDER` before the `STORAGES` block references them, so the storage backend classes do not raise `AttributeError`.

#### Scenario: S3 branch defines location variables
- **WHEN** `STORAGE_AWS` is true and a reader follows `django-project-setup.md` Step 7
- **THEN** `STATIC_LOCATION`, `PUBLIC_MEDIA_LOCATION`, and `PRIVATE_MEDIA_LOCATION` SHALL be defined as `<AWS_PROJECT_FOLDER>/static`, `<AWS_PROJECT_FOLDER>/media`, and `<AWS_PROJECT_FOLDER>/private`

#### Scenario: Cross-reference to storage guide
- **WHEN** the reader reaches the storage section of `django-project-setup.md`
- **THEN** a note SHALL point to `django-media-storage.md` for the full storage guide

### Requirement: Private storage available in local development
The local `STORAGES` fallback in `docs/django-project-setup.md` Step 7 SHALL include a `private` backend using `FileSystemStorage` so code referencing `settings.STORAGES["private"]` works in development.

#### Scenario: Local fallback includes private backend
- **WHEN** `STORAGE_AWS` is false and a reader follows `django-project-setup.md` Step 7
- **THEN** the local `STORAGES` dict SHALL define a `private` entry with backend `django.core.files.storage.FileSystemStorage` writing under a `private-media/` subfolder of `MEDIA_ROOT`

### Requirement: Docker ARG list complete in media storage guide
The Docker snippet in `docs/django-media-storage.md` SHALL declare all S3-related build ARGs used by the storage configuration, matching `django-project-setup.md`.

#### Scenario: Docker snippet lists all S3 ARGs
- **WHEN** a reader follows the Docker/CI section of `django-media-storage.md`
- **THEN** the build ARGs SHALL include `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_STORAGE_BUCKET_NAME`, `AWS_S3_REGION_NAME`, `AWS_S3_ENDPOINT_URL`, `AWS_S3_CUSTOM_DOMAIN`, `AWS_PROJECT_FOLDER`, and `STORAGE_AWS`

### Requirement: Consistent project naming
`docs/django-drf.md` SHALL use `project` as the Django project package name everywhere (settings, pagination, handlers, urls), matching `django-project-setup.md`.

#### Scenario: No myproject references remain
- **WHEN** a reader searches `docs/django-drf.md` for `myproject`
- **THEN** no occurrences SHALL remain; the package is referenced as `project`

### Requirement: Model choices use a sequence
Sample models in `docs/django-drf.md` SHALL define `choices` as a `models.TextChoices` subclass, not a plain dict, following Django idiom.

#### Scenario: Sample model defines TextChoices
- **WHEN** a reader copies the sample `Article` model from `docs/django-drf.md` §8.1
- **THEN** the language field SHALL use a `models.TextChoices` subclass with `choices=Lang.choices` and `default=Lang.EN`

### Requirement: Spanish-only asset documented only in Spanish recipe
The `range_date_filter_es.js` script tag SHALL be removed from the default `admin/base.html` template in `docs/django-project-setup.md` and SHALL be documented in `docs/django-i18n-es-admin.md` instead, since the default project is English.

#### Scenario: English setup has no Spanish script
- **WHEN** a reader follows `django-project-setup.md` Step 10
- **THEN** the `admin/base.html` template SHALL NOT include `range_date_filter_es.js`

#### Scenario: Spanish recipe documents the script
- **WHEN** a reader follows `docs/django-i18n-es-admin.md`
- **THEN** the Spanish admin recipe SHALL document the `range_date_filter_es.js` script as part of localizing date filter placeholders

### Requirement: Consistent logo filename
The docs SHALL reference `logo.webp` consistently for the Unfold `SITE_LOGO`, matching `django-unfold-admin.md`.

#### Scenario: Project setup references webp logo
- **WHEN** a reader follows `django-project-setup.md` Step 11
- **THEN** the logo file SHALL be named `logo.webp` (not `logo.svg`)
