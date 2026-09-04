## Why

Agents and contributors intermittently invoke `pytest`/`pytest-django` (system `pytest 7.4.4` exists outside `venv`, stale specs reference `conftest.py`, and LLMs default to pytest) while the project intentionally uses only Django's integrated runner `python manage.py test` via `project/settings.py:88` (`IS_TESTING = sys.argv[1]=="test"`). The mismatch creates 42 phantom `Missing staticfiles manifest` failures under pytest and spec drift (`openspec/specs/admin-list-performance:132`). Locking the repo to Django tests removes ambiguity for current code and all future changes.

## What Changes

- **Agent contract:** Add a `Testing — Django only` section to `AGENTS.md` declaring the canonical runner `venv/bin/python manage.py test`, listing the only approved test bases (`django.test.TestCase`, `rest_framework.test.APITestCase`/`APIClient`, `RequestFactory`, `override_settings`), and explicitly banning `pytest`, `pytest-django`, `conftest.py`, `pytest.ini`/`.pytest.ini`, `setup.cfg [tool:pytest]`, `pyproject.toml [tool.pytest]`, and `import pytest`.
- **Spec sync (modified capability):** Update `admin-list-performance` requirement from “SHALL provide pytest `conftest.py`” to “SHALL render admin via Django's `IS_TESTING` → `StaticFilesStorage` fallback in `project/settings.py:203` without any pytest fixture” (production whitenoise behavior unchanged).
- **New capability:** Introduce `testing-contract` capability that documents the allowed runner, DB isolation (`testing.sqlite3`), and verification steps; it becomes the single source of truth for humans, agents, and CI.
- **Repo shape hardening:** Rely on existing `.*/` at `.gitignore:57` to ignore `.pytest_cache/` etc. (no explicit `/.pytest_cache/`, `/conftest.py`, `/pytest.ini` entries — minimal file, per review decision); ensure `/.venv/` alongside `venv` at `.gitignore:12-14` for completeness, ensure `requirements.txt` stays without pytest deps (selenium remains the only testing extra), and remove any residual `conftest.py`/`pytest.ini` artifacts.
- **Mechanical enforcement (Option D — full guard):** Add a CI gate (shell script `.opencode/commands/guard.sh` as single source of truth + GitHub Actions workflow `.github/workflows/test-contract.yml` invoking it) that (1) fails if `pytest`/`pytest-django` appears in `pip freeze` or `requirements*.txt`, (2) fails if `conftest.py`/`pytest.ini`/`.pytest.ini`/`setup.cfg` with `[tool:pytest]`/`pyproject.toml` with `[tool.pytest]` is added, (3) fails if any `*.py` imports `pytest` or uses `@pytest.*`, and (4) fails if any `openspec/changes/*/tasks.md` (non-archive) contains a `pytest` command. Gate runs in CI before `manage.py test` and is invocable locally via the guard script (strict Option D — no Makefile/pre-commit wrapper).
- **Docs alignment:** Clarify `docs/django-project-setup.md:378-386` and `docs/testing-stripe.md` to reference only `python manage.py test` (already present, just made explicit).

## Capabilities

### New Capabilities
- `testing-contract`: Contract for the Django-only test runner, database isolation, allowed test utilities, anti-pytest bans, and enforcement gate. Creates `specs/testing-contract/spec.md`.

### Modified Capabilities
- `admin-list-performance`: Requirement “Admin views render under pytest without a staticfiles manifest” is replaced with “Admin views render during Django tests without a staticfiles manifest via IS_TESTING fallback” — removes `conftest.py`/`pytest` language, preserves the “Missing manifest” guarantee and production whitenoise clause. Purpose line “admin views remain testable under pytest…” in `openspec/specs/admin-list-performance/spec.md:6-8` SHALL also be updated to “admin views remain testable during Django tests via IS_TESTING fallback…”. Needs delta spec at `specs/admin-list-performance/spec.md`.

## Impact

- **AGENTS.md:1** — new `## Testing — Django only` section (agents, Opencode, Muse Spark read on session start).
- **openspec/specs/testing-contract/spec.md** — new spec (4 requirements, 15 scenarios).
- **openspec/specs/admin-list-performance/spec.md** — MODIFIED delta (1 requirement rewritten, 2 scenarios updated).
- **.gitignore:12-14** — `/.venv/` alongside `venv`/`.venv`; `.*/` at `.gitignore:57` already covers `.pytest_cache/` (no explicit pytest ignores per review decision).
- **CI config** — shell script `.opencode/commands/guard.sh` (single source) + workflow `.github/workflows/test-contract.yml` invoking it as job `test-contract-guard` before `manage.py test`; strict Option D, no Makefile/pre-commit wrapper.
- **requirements.txt:18** — unchanged (assertion that pytest deps are absent is part of guard).
- **No runtime code change** to `artworks/tests.py`, `blog/tests.py`, `subscriptions/tests.py`, `project/settings.py` (settings already correct at `project/settings.py:88` and `203-214`); only docs/specs/guard added.
- **Breaking:** Any local workflow that relied on `pytest` will now fail the gate (intentional). Migration is `pytest X` → `python manage.py test X --verbosity=2`.
