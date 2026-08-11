## 1. Hub index (spec: docs-hub-completeness)

- [x] 1.1 Add links to `django-fixtures`, `django-redis`, `django-local-subdomain-setup`, and `django-i18n-es-admin` to the Internal Resources section of `docs/django.md`
- [x] 1.2 Add a wikilink portability convention section to `docs/django.md` documenting how agents must handle `[[wikilinks]]` when copying docs into new Django projects (short-form sibling links stay as-is, vault-path sibling links convert to short-form, external `30-resources/*` links become plain text labels)

## 2. Config coherence — project setup (spec: docs-config-coherence)

- [x] 2.1 Add `STATIC_LOCATION`, `PUBLIC_MEDIA_LOCATION`, `PRIVATE_MEDIA_LOCATION` computations to the S3 branch of Step 7 in `docs/django-project-setup.md` (`f"{AWS_PROJECT_FOLDER}/..."`), with a cross-reference note to `docs/django-media-storage.md`
- [x] 2.2 Add a `private` entry (`FileSystemStorage`, under a `private-media/` subfolder of `MEDIA_ROOT`) to the local `STORAGES` fallback in Step 7 of `docs/django-project-setup.md`
- [x] 2.3 Change the logo reference in Step 11 of `docs/django-project-setup.md` from `logo.svg` to `logo.webp`
- [x] 2.4 Remove the `range_date_filter_es.js` script tag from the `admin/base.html` template in Step 10 of `docs/django-project-setup.md`

## 3. Config coherence — media storage & drf (spec: docs-config-coherence)

- [x] 3.1 Add `AWS_S3_REGION_NAME`, `AWS_S3_CUSTOM_DOMAIN`, and `AWS_PROJECT_FOLDER` to the Docker build-args snippet in `docs/django-media-storage.md`
- [x] 3.2 Rename `myproject` → `project` throughout `docs/django-drf.md` (settings paths, pagination, handlers, urls, quick reference, checklist)
- [x] 3.3 Replace the `LANGS` dict with a `models.TextChoices` subclass in the sample `Article` model of `docs/django-drf.md` §8.1 (add `class Lang(models.TextChoices)` with `EN`/`ES`, use `choices=Lang.choices, default=Lang.EN`)

## 4. Deploy/admin coherence (spec: docs-deploy-admin-coherence)

- [x] 4.1 Add `python manage.py base_loaddata` (with a comment that base data is required for the system to function) to `start.sh` after the migrate steps in Step 14 of `docs/django-project-setup.md`
- [x] 4.2 Replace `python manage.py makemigrations --noinput` with `python manage.py makemigrations --check --noinput` in `start.sh`, and add a note to run `makemigrations` locally before building the Docker image and commit the resulting files
- [x] 4.3 Add `import project.admin` with an explanatory comment to the `urls.py` template in Step 10 of `docs/django-project-setup.md`
- [x] 4.4 Replace the full `project/admin.py` code block in Step 10 of `docs/django-project-setup.md` with a reference to `docs/django-unfold-admin.md` §7.1 (keep the DRF-only conditional note)

## 5. Admin wiring — unfold guide (spec: docs-deploy-admin-coherence)

- [x] 5.1 Verify `docs/django-unfold-admin.md` §7.1 still contains the full `UserAdmin`/`GroupAdmin`/`TokenAdmin` code and the `import project.admin` requirement (no edits expected; single canonical copy)

## 6. Formatting (spec: docs-formatting)

- [x] 6.1 In `docs/django-unfold-admin.md` §3.1, move the orphaned sentence ("No `permission` callback, no Python helper, no custom `AdminSite` subclass, and no `core/admin.py` changes are required.") inside the code block as a comment
- [x] 6.2 Normalize links in `docs/django-redis.md`: short-form `[[name|label]]` for docs in this folder, plain text labels for external vault resources (e.g. `Redis (external)` for `[[30-resources/redis/redis|Redis]]`, `PostgreSQL (external)` for `[[30-resources/postgresql/postgresql|PostgreSQL]]`, `Coolify (external)` for `[[30-resources/docs/coolify-services|Coolify Services]]`)

## 7. Spanish recipe (spec: docs-config-coherence)

- [x] 7.1 Add documentation of the `range_date_filter_es.js` script (localizing Unfold range-date-filter placeholders) to `docs/django-i18n-es-admin.md` so the script reference removed in task 2.4 is covered there

## 8. Verification

- [x] 8.1 Re-read each edited section and confirm the code samples are valid Python/bash/JSON and match the invariants in the specs
- [x] 8.2 Confirm no `myproject` references remain in `docs/django-drf.md` and the hub lists all 10 docs
