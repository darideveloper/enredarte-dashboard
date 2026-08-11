## ADDED Requirements

### Requirement: Base data loads at container startup
The `start.sh` template in `docs/django-project-setup.md` SHALL run `python manage.py base_loaddata` after `migrate` and before starting Gunicorn, matching the contract in `docs/django-fixtures.md`, with a comment explaining base data is required for the system to function.

#### Scenario: start.sh loads base data
- **WHEN** a reader follows `django-project-setup.md` Step 14
- **THEN** `start.sh` SHALL contain `python manage.py base_loaddata` after the migrate step and a comment noting base data is required for the system to work

### Requirement: Migrations validated, not generated, at container startup
The `start.sh` template in `docs/django-project-setup.md` SHALL NOT run `makemigrations` in generation mode at runtime.

#### Scenario: start.sh validates migrations
- **WHEN** a reader follows `django-project-setup.md` Step 14
- **THEN** the `start.sh` SHALL run `python manage.py makemigrations --check --noinput` (validating, failing loudly if migrations are missing) instead of `makemigrations --noinput`

#### Scenario: Pre-deploy migration note
- **WHEN** a reader follows `django-project-setup.md` Step 14
- **THEN** a note SHALL instruct running `makemigrations` locally before building the Docker image and committing the resulting migration files

### Requirement: Custom admin registered via explicit import
The `urls.py` template in `docs/django-project-setup.md` SHALL import `project.admin` explicitly with a comment, so the custom `UserAdmin`/`GroupAdmin`/`TokenAdmin` classes register as documented in `django-unfold-admin.md`.

#### Scenario: urls.py imports project.admin
- **WHEN** a reader follows `django-project-setup.md` Step 10
- **THEN** `urls.py` SHALL contain `import project.admin` with a comment explaining that the project package is not in `INSTALLED_APPS` and Django does not auto-discover its admin module

### Requirement: Single canonical copy of project/admin.py
The full `project/admin.py` code block SHALL live only in `docs/django-unfold-admin.md`; `docs/django-project-setup.md` Step 10 SHALL reference it instead of duplicating the code.

#### Scenario: Project setup references admin code
- **WHEN** a reader follows `django-project-setup.md` Step 10
- **THEN** it SHALL link to `django-unfold-admin.md` for the `project/admin.py` code rather than re-printing the full block

#### Scenario: Unfold guide keeps the code
- **WHEN** a reader follows `docs/django-unfold-admin.md` §7.1
- **THEN** the full `UserAdmin`/`GroupAdmin`/`TokenAdmin` code with the `import project.admin` requirement SHALL be present
