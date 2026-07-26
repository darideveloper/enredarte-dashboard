## ADDED Requirements

### Requirement: Storage backend classes
The system SHALL create `project/storage_backends.py` with three classes inheriting from `storages.backends.s3boto3.S3Boto3Storage`:
- `StaticStorage`: `location=settings.STATIC_LOCATION`, `default_acl="public-read"`
- `PublicMediaStorage`: `location=settings.PUBLIC_MEDIA_LOCATION`, `default_acl="public-read"`, `file_overwrite=False`
- `PrivateMediaStorage`: `location=settings.PRIVATE_MEDIA_LOCATION`, `default_acl="private"`, `file_overwrite=False`, `custom_domain=False`

#### Scenario: Backend classes importable
- **WHEN** the project imports `project.storage_backends.PublicMediaStorage`
- **THEN** the class SHALL resolve without import errors

### Requirement: Conditional STORAGES configuration
The system SHALL define a `STORAGES` dict in `settings.py` that switches between S3 backends and local storage based on `STORAGE_AWS` env var. When `STORAGE_AWS=True`, it SHALL map `default` to `PublicMediaStorage`, `staticfiles` to `StaticStorage`, and `private` to `PrivateMediaStorage`. When `STORAGE_AWS=False`, it SHALL map `default` to `FileSystemStorage` and `staticfiles` to `CompressedManifestStaticFilesStorage`.

#### Scenario: Local storage active in dev
- **WHEN** `STORAGE_AWS=False`
- **THEN** uploaded files SHALL be stored in `MEDIA_ROOT` (local filesystem)

#### Scenario: S3 storage active in prod
- **WHEN** `STORAGE_AWS=True` and AWS credentials are set
- **THEN** `collectstatic` SHALL upload to S3 and file uploads SHALL go to the configured bucket

### Requirement: AWS environment variables
The system SHALL declare AWS-related env vars in `.env.prod`: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_STORAGE_BUCKET_NAME`, `AWS_PROJECT_FOLDER`, `AWS_S3_REGION_NAME`, `AWS_S3_ENDPOINT_URL`, `AWS_S3_CUSTOM_DOMAIN`. These SHALL be empty strings in the template file, to be filled at deploy time.

#### Scenario: Prod env file has AWS placeholders
- **WHEN** `.env.prod` is inspected
- **THEN** all AWS variables SHALL exist with empty values, ready for deployment configuration

### Requirement: AWS settings from environment
When `STORAGE_AWS=True`, the system SHALL read `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_STORAGE_BUCKET_NAME`, `AWS_S3_ENDPOINT_URL`, `AWS_S3_REGION_NAME`, `AWS_S3_CUSTOM_DOMAIN`, and `AWS_PROJECT_FOLDER` from environment variables. It SHALL compute `STATIC_LOCATION`, `PUBLIC_MEDIA_LOCATION`, and `PRIVATE_MEDIA_LOCATION` as `{AWS_PROJECT_FOLDER}/static`, `{AWS_PROJECT_FOLDER}/media`, `{AWS_PROJECT_FOLDER}/private`. It SHALL set `AWS_S3_OBJECT_PARAMETERS={"CacheControl": "max-age=86400"}` and `AWS_DEFAULT_ACL=None`.

#### Scenario: Folder locations computed
- **WHEN** `AWS_PROJECT_FOLDER="enredarte"`
- **THEN** `STATIC_LOCATION` SHALL be `enredarte/static`, `PUBLIC_MEDIA_LOCATION` SHALL be `enredarte/media`

### Requirement: get_media_url utility
The system SHALL create `utils/media.py` with a `get_media_url(object_or_url)` function that returns an absolute URL. If the input is a model instance with a `url` attribute, it SHALL extract `object_or_url.url`. If the URL does NOT contain `s3.amazonaws.com` or `digitaloceanspaces`, it SHALL prepend `settings.HOST` to make it absolute. If the URL already contains a cloud domain, it SHALL return it unchanged.

#### Scenario: Local URL made absolute
- **WHEN** `settings.HOST=http://localhost:8000` and a file URL is `/media/uploads/img.jpg`
- **THEN** `get_media_url` SHALL return `http://localhost:8000/media/uploads/img.jpg`

#### Scenario: S3 URL returned unchanged
- **WHEN** a file URL contains `s3.amazonaws.com`
- **THEN** `get_media_url` SHALL return the URL as-is without prepending `settings.HOST`

### Requirement: Image copy link JavaScript
The system SHALL create `static/js/copy_clipboard.js` that, on `DOMContentLoaded`, extracts the `copy_to_clipboard` cookie value, copies it to the clipboard using `navigator.clipboard.writeText()`, and immediately clears the cookie. It SHALL strip surrounding double-quotes from the cookie value before copying.

#### Scenario: Cookie triggers clipboard copy
- **WHEN** the page loads and `copy_to_clipboard` cookie exists with value `http://localhost:8000/media/img.jpg`
- **THEN** the URL SHALL be copied to the system clipboard and the cookie SHALL be deleted

#### Scenario: No cookie means no action
- **WHEN** the page loads and `copy_to_clipboard` cookie does NOT exist
- **THEN** no clipboard operation SHALL occur

### Requirement: get_test_image utility
The system SHALL create `utils/media.py` with a `get_test_image(image_name="test.webp")` function that reads an image from `media/` directory and returns a `SimpleUploadedFile`. The function SHALL resolve paths relative to the project root from the utility's own file location.

#### Scenario: Test image created
- **WHEN** `get_test_image()` is called and `media/test.webp` exists
- **THEN** a `SimpleUploadedFile` with content_type `image/webp` SHALL be returned

### Requirement: Image admin copy link action ready
The system SHALL document in `utils/media.py` that the `get_media_url` function, combined with the `@action` decorator from `unfold.decorators` and the cookie-based clipboard pattern from `copy_clipboard.js`, provides a complete server-to-client copy mechanism available for any `ModelAdmin` with an image field. No model-specific admin SHALL be created yet — the utilities are infrastructure only.

#### Scenario: Future model can use copy link
- **WHEN** a developer creates an admin for a model with an image field
- **THEN** they SHALL be able to add a `copy_link` action using `get_media_url`, `redirect`, `response.set_cookie`, and including `copy_clipboard.js` in the admin's `Media` class
