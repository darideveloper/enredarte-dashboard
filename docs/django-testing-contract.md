---
created: 2026-09-04
updated: 2026-09-04
tags:
  - django
  - testing
  - documentation
type: guide
status: active
---

# Django Testing Contract — Django-only Runner

> Drop-in guide to lock **any** Django project to `python manage.py test` and prevent `pytest`/`pytest-django` (or any alternative runner) from creeping back — via docs, settings, gitignore, and a mechanical CI guard. Copy-paste ready.

This is the replicable version of what was done in `enredarte-dashboard` (`openspec/changes/archive/2026-09-04-enforce-django-test-only`). It fixes the 3 root causes that invited pytest drift: **(1)** system `pytest` outside `venv`, **(2)** stale spec `conftest.py` reference, **(3)** LLMs defaulting to `pytest`.

## Rule

**Canonical runner:** `venv/bin/python manage.py test [--verbosity=2]` (or `python manage.py test` when venv active). Targeted: `venv/bin/python manage.py test <app>.tests.<Case>.<test> --verbosity=2`. Never `pytest`, `python -m pytest`, `pytest -k`.

**Allowed:** `django.test.TestCase`, `rest_framework.test.APITestCase`/`APIClient`, `RequestFactory`, `override_settings`, `SimpleUploadedFile`, `call_command`, stdlib (`unittest.mock`, `base64`, `hashlib`, `hmac`, `Decimal`, `json`), `selenium` only testing extra.

**Banned:** `pytest`, `pytest-django`, `conftest.py`, `pytest.ini`/`.pytest.ini`, `setup.cfg [tool:pytest]`, `pyproject.toml [tool.pytest]`/`[tool.pytest.ini_options]`, any `import pytest`/`from pytest`/`@pytest.*` in `*.py`. Do not create `pyproject.toml`/`setup.cfg` with `[tool.pytest]` to "disable" pytest — absence is the ban.

## Replicate in 6 steps (copy-paste)

### 1. `AGENTS.md` — single source for humans + agents

Add after existing conventions (agents load this on session start):

```markdown
## Testing — Django only

Canonical runner: `venv/bin/python manage.py test [--verbosity=2]` (or `python manage.py test` when venv is active). Use Django test labels for targeted runs, e.g. `venv/bin/python manage.py test subscriptions.tests.AdminEndpointTest.test_sync_from_stripe_reconciles_state --verbosity=2` — do not use pytest nodeids (`-k`).

Allowed bases/helpers: `django.test.TestCase`, `rest_framework.test.APITestCase` / `APIClient`, `django.test.RequestFactory`, `django.test.override_settings`, `django.core.files.uploadedfile.SimpleUploadedFile`, `django.core.management.call_command`, and stdlib helpers (`unittest.mock`, `base64`, `hashlib`, `hmac`, `Decimal`, `json`). Only testing extra in `requirements.txt:18` is `selenium`.

**Banned:** `pytest`, `pytest-django`, `conftest.py`, `pytest.ini`/`.pytest.ini`, `setup.cfg` with `[tool:pytest]`, `pyproject.toml` with `[tool.pytest]` / `[tool.pytest.ini_options]`, and any `import pytest` / `from pytest` / `@pytest.*` in `*.py`. Do not add `conftest.py`, `pytest.ini`, or pytest config. The contract is enforced by `.opencode/commands/guard.sh` and CI job `test-contract-guard` (see `openspec/specs/testing-contract/spec.md`). References: `project/settings.py:88` (`IS_TESTING`) and `project/settings.py:203-214` (StaticFilesStorage fallback).
```

Why `AGENTS.md` over `CONTRIBUTING.md` or `.opencode/AGENTS.md`: lowest friction, already loaded by agents, versioned. A sub-scope twin is redundant unless scope diverges. A hook that rewrites `pytest` → `manage.py test` was rejected — it hides rather than teaches.

### 2. `project/settings.py` — DB + staticfiles isolation (already correct here, copy if missing)

```python
import sys
IS_TESTING = len(sys.argv) > 1 and sys.argv[1] == "test"

if IS_TESTING:
    DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "testing.sqlite3"}}
else:
    # ... normal DB_ENGINE / DB_* logic
    pass

# STORAGES: avoid Whitenoise manifest during tests
if STORAGE_AWS:
    STORAGES = {"default": {"BACKEND": "project.storage_backends.PublicMediaStorage"}, "staticfiles": {"BACKEND": "project.storage_backends.StaticStorage"}, "private": {"BACKEND": "project.storage_backends.PrivateMediaStorage"}}
else:
    staticfiles_backend = "django.contrib.staticfiles.storage.StaticFilesStorage" if IS_TESTING else "whitenoise.storage.CompressedManifestStaticFilesStorage"
    STORAGES = {
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": staticfiles_backend},
        # add private storage even locally if you use it
        "private": {"BACKEND": "django.core.files.storage.FileSystemStorage", "OPTIONS": {"location": MEDIA_ROOT / "private-media"}},
    }
```

> No `conftest.py` fixture needed. Admin changelist/change/add views render 200 during `manage.py test` because `StaticFilesStorage` doesn't need `staticfiles.json`. Production stays on `CompressedManifestStaticFilesStorage`. No runtime change to existing `TestCase`/`APITestCase` suites.

### 3. `.gitignore` — minimal (Ponytail)

```gitignore
venv
.venv
/.venv/
# ... existing
.*/        # already covers .pytest_cache and any dotfile (e.g. .pytest.ini) — canonical per D3
```

- Do **not** add explicit `/.pytest_cache/` or `/conftest.py` — `.*/` handles dotfiles; `conftest.py`/`pytest.ini` (no dot) intentionally not gitignored — blocked by the guard instead (fail-loud > silent ignore). Per `design.md:35` D3 this was a deliberate minimal-file decision (review 2026-09-03).
- Verification (proves `.*/` works, don't grep `.gitignore`):
  ```bash
  touch .hidden_test_file && git check-ignore -v .hidden_test_file  # → .gitignore:57:.*/
  touch .pytest_cache && git check-ignore -v .pytest_cache          # → .*/ (dotfile)
  touch .pytest.ini && git check-ignore -v .pytest.ini              # → .*/ (dotfile)
  # conftest.py / pytest.ini (no dot) intentionally NOT ignored — guard.sh fails them
  ```

### 4. `requirements.txt` — no pytest deps

```text
# testing
selenium>=4.40.0   # only testing extra — no pytest/pytest-django
```

Ensure `grep -i pytest requirements.txt` is empty (also check `requirements-dev.txt` if it exists). Never add `pytest`/`pytest-django` even to `requirements-dev.txt` — it signals endorsement.

### 5. Mechanical guard — `.opencode/commands/guard.sh` (single source of truth)

> **Important:** repo `.gitignore` has `.*/` which ignores hidden folders (`.opencode`, `.github`). Commit guard + workflow with `git add -f`. Absence of `pyproject.toml`/`setup.cfg` **is** the ban — don't create an empty `[tool.pytest]` config to "disable" pytest (`design.md:49` D5).

Create `chmod +x .opencode/commands/guard.sh` (4 checks — `design.md:41` D4, strict Option D, no Makefile/pre-commit):

```sh
#!/bin/sh
# guard.sh — testing-contract gate (single source of truth)
# Fails if pytest is reintroduced. See openspec/specs/testing-contract/spec.md
set -eu
fail=0
say_fail() { echo "FAIL: $1" >&2; fail=1; }
for f in requirements.txt requirements-dev.txt; do
  if [ -f "$f" ] && grep -qi "pytest" "$f" 2>/dev/null; then say_fail "pytest found in $f"; grep -in "pytest" "$f" >&2 || true; fi
done
pip_freeze=""
for cand in "venv/bin/pip freeze" ".venv/bin/pip freeze" "pip freeze" "python -m pip freeze" "python3 -m pip freeze"; do
  if echo "$cand" | grep -q "venv/bin/pip"; then bin=$(echo "$cand" | awk '{print $1}'); if [ -x "$bin" ]; then if pip_freeze=$($bin freeze 2>/dev/null); then break; fi; fi
  elif echo "$cand" | grep -q ".venv/bin/pip"; then bin=$(echo "$cand" | awk '{print $1}'); if [ -x "$bin" ]; then if pip_freeze=$($bin freeze 2>/dev/null); then break; fi; fi
  else if pip_freeze=$(sh -c "$cand" 2>/dev/null); then break; fi; fi
done
if echo "$pip_freeze" | grep -qi "pytest" 2>/dev/null; then say_fail "pytest found in pip freeze"; echo "$pip_freeze" | grep -i "pytest" >&2 || true; fi
found_files=$(find . \( -path "./.git/*" -o -path "./.venv/*" -o -path "./venv/*" -o -path "./openspec/changes/archive/*" -o -path "./.opencode/node_modules/*" \) -prune -o \( -name "conftest.py" -o -name "pytest.ini" -o -name ".pytest.ini" \) -print 2>/dev/null || true)
if [ -n "$found_files" ]; then say_fail "banned file found (conftest.py/pytest.ini/.pytest.ini)"; echo "$found_files" >&2; fi
if [ -f "setup.cfg" ] && grep -q "\[tool:pytest" setup.cfg 2>/dev/null; then say_fail "banned [tool:pytest] in setup.cfg"; grep -n "\[tool:pytest" setup.cfg >&2 || true; fi
if [ -f "pyproject.toml" ] && grep -q "\[tool.pytest" pyproject.toml 2>/dev/null; then say_fail "banned [tool.pytest] in pyproject.toml"; grep -n "\[tool.pytest" pyproject.toml >&2 || true; fi
import_hits=$(grep -R --include="*.py" -nE "^\s*(import pytest|from pytest|@pytest\.)" --exclude-dir=.git --exclude-dir=.venv --exclude-dir=venv --exclude-dir=node_modules . 2>/dev/null | grep -v "openspec/changes/archive/" || true)
if [ -n "$import_hits" ]; then say_fail "banned pytest import/decorator in *.py"; echo "$import_hits" >&2; fi
raw_task_hits=$(grep -R -nE "python -m pytest|pytest -k|(^| )pytest( [A-Za-z0-9_/\.-]|$)" openspec/changes --include="tasks.md" 2>/dev/null | grep -v "openspec/changes/archive/" || true)
task_hits=$(echo "$raw_task_hits" | grep -v -i "banning" | grep -v -i "banned" | grep -v "grep.*pytest" | grep -v "no pytest" | grep -v "import.*pytest" | grep -v "contains no instruction" || true)
if [ -n "$task_hits" ]; then say_fail "pytest command in openspec/changes/*/tasks.md (non-archive)"; echo "$task_hits" >&2; fi
if [ "$fail" -ne 0 ]; then echo "test-contract-guard FAILED" >&2; exit 1; fi
echo "test-contract-guard OK"
```

Local: `./.opencode/commands/guard.sh` must exit 0. Negative test: `echo 'raise' > conftest.py && ./.opencode/commands/guard.sh` → `FAIL: banned file found ./conftest.py`, then `rm conftest.py && ./.opencode/commands/guard.sh` → `OK`. Also valid for nested `app/conftest.py`.

### 6. CI — `.github/workflows/test-contract.yml` (guard-only — tests run local/prod, not GitHub)

```yaml
name: test-contract
on: [push, pull_request]
jobs:
  test-contract-guard:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: chmod +x .opencode/commands/guard.sh && ./.opencode/commands/guard.sh
```

Tests run **local** (`venv/bin/python manage.py test --verbosity=2`) and **prod** (manual/deploy), not in GitHub — this workflow only enforces the Django-only contract. Previous version with `test:` job (`needs: test-contract-guard` → `python manage.py test`) was removed to avoid `SECRET_KEY`/`.env.dev` drift (gitignored) and 90s CI suite cost.

Set branch protection: `test-contract-guard` = **required** (PR cannot merge when red) — mitigates guard bypass (`design.md:62`). Commit both files with `git add -f .opencode/commands/guard.sh .github/workflows/test-contract.yml` (otherwise `.*/` ignores them). No `Makefile`/`make test` or pre-commit wrapper — canonical remains `venv/bin/python manage.py test` only. To re-enable CI tests later, re-add a `test:` job with `needs: test-contract-guard` + `env: SECRET_KEY=test...` and `pip install -r requirements.txt`.

## Breaking & Migration

**Breaking:** Any local workflow that relied on `pytest` will now fail the gate intentionally (`proposal.md:31`). This is desired — the 42 `Missing staticfiles manifest` failures under pytest are gone only under the Django runner.

| Before | After |
|--------|-------|
| `pytest` / `pytest -k test_foo` / `python -m pytest` | `venv/bin/python manage.py test --verbosity=2` / `venv/bin/python manage.py test app.tests.Case.test_foo --verbosity=2` |

**Migration Plan** (`design.md:65`):
1. Merge `AGENTS.md` + `.gitignore` + specs + CI guard in one PR (no DB migration, no runtime code change to `artworks/tests.py` etc.).
2. Clean local: `rm -rf .pytest_cache conftest.py pytest.ini .pytest.ini` (if present).
3. Subsequent PRs: agents copy-pasting `pytest <path>` will get CI red; fix is `venv/bin/python manage.py test <path> --verbosity=2`.
4. Rollback: revert the 4-file change; no stateful side effects.

## Spec & Docs alignment (done in this project)

- `docs/django-project-setup.md:384-389` validation block now says `python manage.py test` is canonical (`do not use pytest`) + callout referencing `openspec/specs/testing-contract/spec.md`.
- `docs/testing-stripe.md:15` header callout referencing testing-contract.
- Specs: new `openspec/specs/testing-contract/spec.md` (4 requirements, 15 scenarios: canonical runner, DB/storage isolation, allowed/banned, enforcement gate) + `openspec/specs/admin-list-performance/spec.md:7` Purpose `under pytest without a staticfiles manifest` → `during Django tests via IS_TESTING fallback` and `132` Requirement `SHALL provide conftest.py` → `SHALL use IS_TESTING → StaticFilesStorage` without fixture (2 scenarios preserved, production whitenoise unchanged). Archive specs (`openspec/changes/archive/2026-08-10-...`) keep pytest language for history.

**If your new project uses OpenSpec**, replicate the spec sync (`tasks.md:5.1-5.3`):
- Create `openspec/specs/testing-contract/spec.md` from delta `specs/testing-contract/spec.md`
- Update `openspec/specs/admin-list-performance/spec.md:7,132` from delta `specs/admin-list-performance/spec.md`
- Run `openspec status --change <name> --json` and `openspec validate <name> --strict` → `valid:true`

## Verification (run after copying)

```bash
venv/bin/python manage.py test --verbosity=2  # expect Ran N tests OK — admin changelist/change/add views 200 (covers admin-list-performance)
./.opencode/commands/guard.sh                 # expect test-contract-guard OK

# Import/file checks (all expect empty / no file)
grep -R --include="*.py" -nE "^\s*(import pytest|from pytest|@pytest\.)" --exclude-dir=.git --exclude-dir=.venv --exclude-dir=venv . | grep -v "openspec/changes/archive/" # expect empty
ls conftest.py pytest.ini 2>&1                # expect no such file
venv/bin/pip freeze | grep -qi pytest && echo "has pytest" || echo "clean"

# .gitignore — dotfiles via .*/
touch .pytest_cache && git check-ignore -v .pytest_cache  # → .gitignore:57:.*/ (dotfile)
touch .pytest.ini && git check-ignore -v .pytest.ini      # → .gitignore:57:.*/ (dotfile)
# conftest.py / pytest.ini (no dot) intentionally NOT ignored — guard FAILs them instead
rm -rf .pytest_cache                          # stale cache from previous pytest runs

# Negative proof
echo 'raise AssertionError("should not be importable")' > conftest.py
./.opencode/commands/guard.sh  # → FAIL: banned file found ./conftest.py
rm conftest.py && ./.opencode/commands/guard.sh  # → OK
```

## Why this works

| Layer | Teaches | Proves |
|-------|---------|--------|
| `AGENTS.md` | agents/humans at session start (Opencode/Muse auto-load) | — |
| `openspec/specs/testing-contract/spec.md` | machine-readable spec for future changes | — |
| `guard.sh` + CI | — | fails PR on any pytest reintroduction (4 checks) |

False positives avoided: import check is anchored `^\s*(import pytest|from pytest|@pytest\.)` (comment `pytest` ok), docs narrative `pytest` allowed (`--include="*.py"` only), archive `openspec/changes/archive/**` allowlisted, task lint only flags command invocations (`pytest <path>`, `python -m pytest`, `pytest -k`) not `grep -i pytest`/`banning pytest` checks.

**Risks & mitigations** (`design.md:54`):
- Agent ignores `AGENTS.md` → CI gate is hard fail (spec is machine-readable fallback).
- System `pytest` remains on dev machines → guard uses fallback chain `venv/bin/pip` → `.venv/bin/pip` → `pip` → `python -m pip` (covers venv/.venv/system).
- CI image without `venv/` → same fallback chain; missing pip still passes file/import checks.
- Future `tasks.md` re-introduces `pytest` wording (`archive/2026-09-03-fix-blog-image-urls:20`) → gate task lint excludes `archive/**` but hard-fails new `tasks.md`.
- Guard bypass via branch protection → `test-contract-guard` required check.
- `CI adds ~5s` → negligible (shell only).

**Non-goals:** No dual runner, no change to test semantics/DB isolation/settings logic (already correct), no coverage/parallel tooling, no porting `TestCase` suites to pytest.

## Adoption checklist for new projects

- [ ] Copy `AGENTS.md` Testing section
- [ ] Copy `project/settings.py` `IS_TESTING` + `STORAGES` fallback (including `private` if used)
- [ ] Add `/.venv/` to `.gitignore` (keep `.*/` at `57` — verify via `git check-ignore`)
- [ ] Ensure `requirements.txt` has no pytest (only `selenium` if needed) — `grep -i pytest` empty
- [ ] Add `guard.sh` + workflow (force-add with `git add -f`), set `test-contract-guard` required in branch protection
- [ ] Update project docs (`django-project-setup.md:384` etc.) — no `pytest` run instructions in `docs/**/*.md`
- [ ] **If using OpenSpec:** create `testing-contract` spec + update `admin-list-performance` Purpose+Requirement, `openspec validate --strict` valid
- [ ] Run verification above (including negative `conftest.py` test)
- [ ] `rm -rf .pytest_cache conftest.py pytest.ini .pytest.ini` locally

## Reference

- Source change: `openspec/changes/archive/2026-09-04-enforce-django-test-only` (proposal/design/specs/tasks still readable after archive)
- Main specs after sync: `openspec/specs/testing-contract/spec.md`, `openspec/specs/admin-list-performance/spec.md:7,132`
- Guard source: `.opencode/commands/guard.sh:1`, workflow: `.github/workflows/test-contract.yml:1`
- See also: [[django-project-setup]] §9 Validation, [[testing-stripe]] §Prerequisites

