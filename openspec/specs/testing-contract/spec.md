# testing-contract

## Purpose
To define the canonical Django-only test runner contract, ensuring all tests use `venv/bin/python manage.py test`, DB and staticfiles isolation via `IS_TESTING`, allowed test utilities, and a mechanical enforcement gate that rejects pytest.

## Requirements

### Requirement: Canonical Django test runner
The system SHALL define `venv/bin/python manage.py test` (and `python manage.py test` when venv is active) as the sole test runner for all current and future tests; alternatives such as `pytest`, `pytest-django`, or `python -m pytest` SHALL be considered unsupported.

#### Scenario: Agent runs the canonical suite
- **WHEN** an agent or contributor needs to run all tests
- **THEN** the command SHALL be `venv/bin/python manage.py test --verbosity=2` and it SHALL exit 0 on a green suite.

#### Scenario: Targeted test execution uses Django test labels
- **WHEN** a single case is needed (e.g., `subscriptions.tests.AdminEndpointTest.test_sync_from_stripe_reconciles_state`)
- **THEN** the runner SHALL support `venv/bin/python manage.py test subscriptions.tests.AdminEndpointTest.test_sync_from_stripe_reconciles_state --verbosity=2` without requiring pytest nodeids (`-k`).

#### Scenario: Pytest invocation is rejected by contract
- **WHEN** a contributor or agent runs `pytest`, `python -m pytest`, or `pytest <path>`
- **THEN** the run SHALL be considered non-canonical and not authoritative for CI, regardless of its exit code.

### Requirement: Django test isolation and storage fallback
The system SHALL use Django's `IS_TESTING = len(sys.argv)>1 and sys.argv[1]=="test"` (`project/settings.py:88`) to select `django.db.backends.sqlite3` at `BASE_DIR/testing.sqlite3` (`project/settings.py:90-96`) and `django.contrib.staticfiles.storage.StaticFilesStorage` for the `staticfiles` backend (`project/settings.py:203-214`), so admin changelist/change/add views render without a Whitenoise `staticfiles.json` manifest.

#### Scenario: Admin renders during Django tests without manifest
- **WHEN** the suite runs via `python manage.py test`
- **THEN** any admin changelist, change, or add view SHALL render with 200 without raising `ValueError: Missing staticfiles manifest entry`.

#### Scenario: Production staticfiles behavior unchanged
- **WHEN** the application runs outside tests (no `test` argv)
- **THEN** `STORAGES["staticfiles"]["BACKEND"]` SHALL remain `whitenoise.storage.CompressedManifestStaticFilesStorage`.

#### Scenario: DB isolation is scoped to argv test mode
- **WHEN** `manage.py` is invoked without `test` (e.g., `runserver`, `migrate`, `collectstatic`)
- **THEN** `DATABASES["default"]` SHALL follow `DB_ENGINE`/`DB_*` env vars and SHALL NOT use `testing.sqlite3`.

### Requirement: Allowed and banned test utilities
The system SHALL ban `pytest`, `pytest-django`, `conftest.py`, `pytest.ini`/`.pytest.ini`, `setup.cfg` with `[tool:pytest]`, `pyproject.toml` with `[tool.pytest]` or `[tool.pytest.ini_options]`, and any `import pytest` / `from pytest` / `@pytest.*` usage in `*.py`; it SHALL otherwise allow stdlib (`unittest.mock`, `base64`, `hashlib`, `hmac`, `Decimal`, `json`), Django (`django.test.TestCase`, `RequestFactory`, `override_settings`, `SimpleUploadedFile`, `call_command`), DRF (`rest_framework.test.APITestCase`, `APIClient`), and `selenium` (`requirements.txt:18`).

#### Scenario: New test uses allowed base
- **WHEN** a contributor adds a test case in `artworks/tests.py`, `blog/tests.py`, `subscriptions/tests.py`, or `core/tests.py`
- **THEN** the case SHALL inherit from `TestCase` or `APITestCase` (or use `RequestFactory`/`override_settings` as helpers) and SHALL NOT use pytest fixtures; stdlib helpers like `unittest.mock.patch` are allowed.

#### Scenario: Banned file appears
- **WHEN** a `conftest.py`, `pytest.ini`/`.pytest.ini`, or `setup.cfg`/`pyproject.toml` containing pytest tool config (`[tool:pytest]` / `[tool.pytest]`) exists at repo root or any package
- **THEN** the contract SHALL be considered violated.

#### Scenario: Banned import appears
- **WHEN** any `*.py` contains `import pytest`, `from pytest import`, or `@pytest.`
- **THEN** the contract SHALL be considered violated.

### Requirement: Enforcement gate (CI / local)
The system SHALL provide a mechanical contract gate that fails the change if (a) `pytest` or `pytest-django` appears in `requirements*.txt` or `pip freeze` (probed via `venv/bin/pip freeze` → `.venv/bin/pip freeze` → `pip freeze` → `python -m pip freeze`), (b) a banned file exists (`conftest.py`, `pytest.ini`/`.pytest.ini` anywhere via `find`, `setup.cfg` containing `[tool:pytest]`, `pyproject.toml` containing `[tool.pytest]`), (c) a banned import/decorator appears in `*.py` (`^\s*(import pytest|from pytest|@pytest\.)` excluding `openspec/changes/archive/**`, `.venv/**`, `venv/**`, `.git`), or (d) a `pytest` *command invocation* (`pytest <path>`, `python -m pytest`, `pytest -k`) appears in any `openspec/changes/*/tasks.md` outside `openspec/changes/archive/**` (narrative mentions like `banning pytest`, `grep -i pytest`, `no pytest deps`, or `contains no instruction to run pytest` are allowlisted); the gate SHALL allow historical mentions of pytest in `openspec/changes/archive/**` and docs narrative `*.md`, and SHALL run in CI before `manage.py test` as required check `test-contract-guard`.

#### Scenario: Gate detects pytest dependency
- **WHEN** `requirements.txt` or `requirements-dev.txt` (if present) or `venv/bin/pip freeze` contains `pytest` (case-insensitive)
- **THEN** the gate SHALL exit non-zero with a message naming the offending file/entry.

#### Scenario: Gate detects banned file
- **WHEN** `conftest.py`, `pytest.ini`/`.pytest.ini` exists anywhere, or `setup.cfg` contains `[tool:pytest` or `pyproject.toml` contains `[tool.pytest`
- **THEN** the gate SHALL exit non-zero naming the path.

#### Scenario: Gate detects banned import
- **WHEN** `grep -R` finds `^\s*(import pytest|from pytest|@pytest\.)` under `--include="*.py"` excluding `openspec/changes/archive/**`, `.venv/**`, `venv/**`, `.git`
- **THEN** the gate SHALL exit non-zero naming the file and line.

#### Scenario: Gate does not flag docs or archives
- **WHEN** the word `pytest` appears only in archive specs (`openspec/changes/archive/**/spec.md`), narrative docs, or comments referencing the historical `conftest`
- **THEN** the gate SHALL NOT fail on those occurrences.

#### Scenario: Future task templates must not reintroduce pytest
- **WHEN** a new change adds `openspec/changes/*/tasks.md` containing a `pytest` command (`pytest`, `python -m pytest`, `pytest -k`) as a verification step
- **THEN** the gate SHALL treat it as a violation unless explicitly allowlisted.

#### Scenario: CI blocks PR on violation
- **WHEN** a PR introduces a violation
- **THEN** CI SHALL mark the `test-contract-guard` job as failed and block merge until the violation is removed or explicitly exempted by the gate allowlist.
