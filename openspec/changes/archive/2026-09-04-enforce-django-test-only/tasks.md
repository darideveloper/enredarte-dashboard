## 1. Agent contract — AGENTS.md

- [x] 1.1 Add `## Testing — Django only` to `AGENTS.md:1` after the model conventions, declaring canonical runner `venv/bin/python manage.py test [--verbosity=2]` (and `python manage.py test` when venv active), allowed bases (`django.test.TestCase`, `rest_framework.test.APITestCase`/`APIClient`, `RequestFactory`, `override_settings`, `SimpleUploadedFile`, `call_command`), and explicitly banning `pytest`, `pytest-django`, `conftest.py`, `pytest.ini`/`.pytest.ini`, `setup.cfg [tool:pytest]`, `pyproject.toml [tool.pytest]`, and any `import pytest`/`@pytest.*`.
- [x] 1.2 Note the only testing extra is `selenium` in `requirements.txt:18`; no pytest deps are added.

## 2. Repo shape hardening

- [x] 2.1 Verify `.*/` at `.gitignore:57` already covers `.pytest_cache/` and dotfiles (`.pytest.ini`, etc.) — no explicit `/.pytest_cache/`, `/conftest.py`, `/pytest.ini` entries (removed per review decision for minimal file; verify via `git check-ignore -v .hidden_test_file` → `.*/`).
- [x] 2.2 Verify `/.venv/` alongside existing `venv` at `.gitignore:12-14` exists (add if missing; decision: keep, strict Option D — `venv`/`/.venv/`/`.venv`).
- [x] 2.3 Ensure `requirements.txt` still contains no `pytest`/`pytest-django` (verify `grep -i pytest requirements.txt` empty); if a `requirements-dev.txt` exists, verify it too.
- [x] 2.4 Clean local artifacts: `rm -rf .pytest_cache conftest.py pytest.ini .pytest.ini` if present (no-op if absent).

## 3. Docs alignment

- [x] 3.1 Verify `docs/django-project-setup.md:378-386` validation block already states `python manage.py test` — add a one-line callout “Canonical; do not use pytest” if not explicit.
- [x] 3.2 Add a one-line note to `docs/testing-stripe.md:1` (or its Prerequisites) referencing the `testing-contract` spec and the canonical `venv/bin/python manage.py test` command.
- [x] 3.3 Confirm `docs/` contains no instruction to run `pytest`/`python -m pytest` (grep `docs/**/*.md`).

## 4. Mechanical enforcement — Option D (full guard, strict)

- [x] 4.1 Create shell script `.opencode/commands/guard.sh` as single source of truth with four checks: (a) Dependency ban: `grep -qi pytest requirements.txt requirements-dev.txt 2>/dev/null` and `pip freeze` fallback chain `venv/bin/pip freeze` → `.venv/bin/pip freeze` → `pip freeze` → `python -m pip freeze` `| grep -qi pytest` → fail naming file; (b) File ban: `find . -name conftest.py -o -name pytest.ini -o -name .pytest.ini | grep -v "^\./.git" | grep -v "^\./.venv" | grep -v "^\./venv" | grep -v "openspec/changes/archive"` or `grep -q "\[tool:pytest" setup.cfg 2>/dev/null` / `grep -q "\[tool.pytest" pyproject.toml 2>/dev/null` → fail naming path; (c) Import ban: `grep -R --include="*.py" -nE "^\s*(import pytest|from pytest|@pytest\.)" --exclude-dir=.git --exclude-dir=.venv --exclude-dir=venv` excluding `openspec/changes/archive/**` → fail naming file:line (anchored, unified); (d) Task lint: pytest *command* invocations only (`pytest <path>`, `python -m pytest`, `pytest -k`) in `openspec/changes/*/tasks.md` outside `openspec/changes/archive/**` → hard fail; narrative mentions (`banning pytest`, `grep -i pytest`, `no pytest deps`, `contains no instruction`) and docs `*.md` are allowlisted. Allowlist: `openspec/changes/archive/**` only.
- [x] 4.2 Create workflow `.github/workflows/test-contract.yml` with job `test-contract-guard` invoking `.opencode/commands/guard.sh`; strict Option D, no Makefile/pre-commit wrapper (canonical runner remains `venv/bin/python manage.py test` only).
- [x] 4.3 Wire CI order: `test-contract-guard` runs before `manage.py test` so a violation fails fast without running the suite; mark `test-contract-guard` as required status check in branch protection.

## 5. Spec sync and validation

- [x] 5.1 Confirm `openspec/changes/enforce-django-test-only/specs/testing-contract/spec.md` covers the 4 requirements (runner, isolation, allowed/banned, gate) with all scenarios present.
- [x] 5.2 Confirm `openspec/changes/enforce-django-test-only/specs/admin-list-performance/spec.md` MODIFIED requirement correctly replaces the `conftest.py`/pytest wording while preserving both scenarios (render without manifest + production whitenoise unchanged) and that the base spec Purpose `openspec/specs/admin-list-performance/spec.md:6-8` will be updated on apply from “under pytest” to “during Django tests via IS_TESTING fallback”.
- [x] 5.3 Run `openspec status --change enforce-django-test-only` and verify no missing artifacts.

## 6. Verification (no code change to runners)

- [x] 6.1 Run Django suite: `venv/bin/python manage.py test --verbosity=2` — expect 0 failures; admin changelist/change/add views render 200 (covers `admin-list-performance` modified requirement).
- [x] 6.2 Run guard and confirm exit 0: `./.opencode/commands/guard.sh` and workflow `.github/workflows/test-contract.yml` job, `grep -R import\ pytest --include="*.py"` empty, `ls conftest.py pytest.ini` missing, `venv/bin/pip freeze | grep -qi pytest` empty.
- [x] 6.3 Negative test: temporarily create `conftest.py` with `raise` and run guard → expect non-zero fail with path named; remove file and re-run → green (proves gate works).
- [x] 6.4 Verify `.gitignore` prevents accidental commit: `touch .pytest_cache && git check-ignore -v .pytest_cache` and `touch .pytest.ini && git check-ignore -v .pytest.ini` should match `.*/` at `.gitignore:57` (dotfiles); `conftest.py`/`pytest.ini` (no dot) are intentionally *not* gitignored — blocked by guard.sh file ban per D3 minimal file.
