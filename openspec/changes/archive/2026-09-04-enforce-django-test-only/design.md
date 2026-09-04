## Context

The codebase has converged on Django's integrated runner: all suites in `artworks/tests.py:9`, `blog/tests.py:6`, `subscriptions/tests.py:13` use `django.test.TestCase`/`APITestCase`, `project/settings.py:88` detects `sys.argv[1]=="test"` to switch DB to `testing.sqlite3` and `project/settings.py:203-214` to `StaticFilesStorage` (avoiding Whitenoise `CompressedManifestStaticFilesStorage` manifest at `staticfiles.json`). The historical pytest path required a project `conftest.py` autouse fixture overriding `STORAGES["staticfiles"]`; it was planned in `openspec/changes/archive/2026-08-10-optimize-admin-performance/design.md:211-223` and deliberately dropped in commit `6f18307` (“drop pytest-only conftest.py (tests run via manage.py test)”) — yet specs still claim `SHALL provide conftest.py` (`openspec/specs/admin-list-performance:132`) and task history references `pytest` (`openspec/changes/archive/2026-09-03-fix-blog-image-urls/tasks.md:20`). System Python has `pytest 7.4.4` + `pytest-django 4.12.0` outside `venv` (`pip show pytest` at `/usr/lib/python3/dist-packages`, `venv/bin/python -m pytest` fails), so an agent invoking bare `pytest` gets stale `Missing staticfiles manifest` failures and stale `.pytest_cache/` (gitignored via `.gitignore:57` `.*/` but still present locally). `AGENTS.md:1-23` currently only documents model `verbose_name/__str__` conventions — no test-runner contract exists.

Stakeholders: LLM agents (Muse Spark, Opencode), human devs, CI, OpenSpec future changes.

## Goals / Non-Goals

**Goals:**
- Make `python manage.py test` the single unambiguous runner for humans, agents, and CI — current and future.
- Close the information vacuum (AGENTS.md) and the contradictory spec (`admin-list-performance:132`) that invite pytest drift.
- Add a mechanical guard (Option D) that fails fast if pytest is reintroduced, without adding pytest deps or runtime logic.

**Non-Goals:**
- Re-introducing pytest/pytest-django or maintaining dual runners.
- Changing test semantics, DB isolation, or `project/settings.py` logic (already correct).
- Adding coverage, parallel, or performance tooling (can be layered later).
- Porting existing `TestCase` suites to pytest style.

## Decisions

### D1 — AGENTS.md as primary contract (over separate doc)
**Choice:** Add `## Testing — Django only` to root `AGENTS.md` (read automatically by Opencode/Muse at session start) rather than a standalone `CONTRIBUTING.md` or `.opencode/` config.
**Why:** Lowest friction; already loaded, versioned, no plugin config. A `.opencode/AGENTS.md` twin is optional but redundant unless a sub-scope diverges.
**Alternative considered:** `.opencode` plugin with a custom hook that rewrites `pytest` → `manage.py test` — rejected as over-engineering for a doc ban; hook would obscure rather than teach.
**Content:** canonical command `venv/bin/python manage.py test` (and `--verbosity=2`, `<app>.tests.<Case>`), allowed imports, explicit bans (`pytest`, `pytest-django`, `conftest.py`, `pytest.ini`/`.pytest.ini`, `setup.cfg [tool:pytest]`, `pyproject.toml [tool.pytest]`, `import pytest`/`@pytest.*`), note that `selenium` is the only testing extra (`requirements.txt:18`).

### D2 — New capability `testing-contract` + delta for `admin-list-performance`
**Choice:** Introduce `specs/testing-contract/spec.md` as source of truth; modify `admin-list-performance` to replace `conftest`-pytest requirement with `IS_TESTING` fallback wording.
**Why:** Separates “how we test” (new capability) from “admin renders without manifest” (existing performance concern) that happened to be conflated via pytest. Future changes reference `testing-contract` without touching admin perf.
**Alternative:** Patch `admin-list-performance` in place only — rejected because it leaves no place for runner/DB/ban invariants.
**Spec shape:** 4 requirements: (1) canonical runner, (2) DB/storage isolation, (3) allowed/banned utilities, (4) enforcement gate.

### D3 — Explicit .gitignore entries vs relying on `.*/`
**Choice:** Rely only on `.*/` at `.gitignore:57` (already catches `.pytest_cache/` and any dotfile) — no explicit `/.pytest_cache/`, `/conftest.py`, `/pytest.ini` entries. `/.venv/` still added alongside `venv` at `.gitignore:12-14` (`venv`/`.venv`/`/.venv/`).
**Why:** Ponytail/minimal: `.*/` already covers the case; explicit lines are redundant and were removed per proposal review decision (2026-09-03). Agents can verify via `touch .pytest_cache && git check-ignore -v .pytest_cache` → `.*/` rather than grepping `.gitignore`; `conftest.py`/`pytest.ini` (no dot) are intentionally not gitignored — blocked by guard file ban.
**Alternative considered:** Add explicit `/.pytest_cache/`, `/conftest.py`, `/pytest.ini`, `/.pytest.ini` for grepability — rejected as redundancy; `.*/` is canonical.

### D4 — Mechanical guard as CI step + workflow, no Makefile (Option D strict)
**Choice:** Shell script `.opencode/commands/guard.sh` as single source of truth + GitHub Actions workflow `.github/workflows/test-contract.yml` job `test-contract-guard` invoking it; strict Option D, no Makefile/pre-commit wrapper.
**Why:** Defense-in-depth: AGENTS.md teaches, spec anchors, CI proves. Four checks in one script: (a) `grep -qi pytest requirements*.txt` and `pip freeze` (tries `venv/bin/pip freeze`, `.venv/bin/pip freeze`, `pip freeze`, `python -m pip freeze` — first available) `| grep -qi pytest`, (b) filesystem `find . -name conftest.py -o -name pytest.ini -o -name .pytest.ini` (excluding `.git`, `.venv`, `venv`, `openspec/changes/archive/**`) and `grep -q "\[tool:pytest" setup.cfg 2>/dev/null` / `grep -q "\[tool.pytest" pyproject.toml 2>/dev/null`, (c) `grep -R --include="*.py" -nE "^\s*(import pytest|from pytest|@pytest\.)" --exclude-dir=.git --exclude-dir=.venv --exclude-dir=venv` excluding `openspec/changes/archive/**` (unified anchored pattern), (d) pytest *command invocation* only (`pytest <path>`, `python -m pytest`, `pytest -k`) via `grep -R -nE "python -m pytest|pytest -k|(^| )pytest( [A-Za-z0-9_/\.-]|$)"` in `openspec/changes --include="tasks.md"` excluding `archive/**` plus allowlist filters for narrative `banning/banned/grep.*pytest/no pytest/contains no instruction` → hard fail on pytest command in new tasks. Fails PR if any hit. Script is invocable locally as `./.opencode/commands/guard.sh`.
**Alternatives:**
- Commit a blocking `conftest.py` that raises — rejected: creates the file we banned, confuses.
- `settings.py` guard `if "pytest" in sys.modules: raise` — rejected: runs too late, couples prod config.
- Adding `pytest` to `requirements-dev.txt` and hoping — rejected: signals endorsement.
- `Makefile` `test`/`test-guard` aliases — rejected per scope decision (strict Option D removes extra files).
**Implementation detail:** Guard probes `pip freeze` via fallback chain `venv/bin/pip freeze` → `.venv/bin/pip freeze` → `pip freeze` → `python -m pip freeze` (first that exists) plus `grep` over repo; no new dependency. Runs before `manage.py test` in CI and is a required status check (`test-contract-guard`) in branch protection.

### D5 — No new `pyproject.toml`/`setup.cfg`
**Choice:** Do not introduce `[tool.pytest]` config to “disable” pytest; absence is the ban.
**Why:** Ponytail: one line before fifty; an empty config is still a config that suggests pytest is supported.
**Alternative:** Add `pyproject.toml` with `tool.pytest.ini_options.addopts = "-p no:warnings"` to make pytest no-op — rejected as misleading.

## Risks / Trade-offs

- **Agent ignores AGENTS.md** → Mitigation: CI gate is hard fail; spec is machine-readable for agents that check `openspec/specs`. Residual: out-of-repo agent without AGENTS.md still drifts — caught on PR.
- **False positive on guard** (e.g., comment mentioning pytest) → Mitigation: guard greps `^\s*(import pytest|from pytest|@pytest\.)` anchored and exact filenames; docs narrative `pytest` mentions allowed via `--exclude-dir` and `archive/**` exclusion (docs `*.md` not matched by `--include="*.py"`).
- **Spec churn** — rewriting `admin-list-performance:132` could be seen as weakening a guarantee → Mitigation: delta spec preserves both scenarios (render without manifest + production whitenoise unchanged) only changing mechanism from `conftest` → `IS_TESTING`.
- **System pytest remains on dev machines** → Mitigation: docs state `venv/bin/python manage.py test`; guard uses fallback pip freeze chain (covers venv, .venv, system) not just `venv/bin/pip`.
- **CI adds ~5s** → Negligible; guard is shell only.
- **Future change templates re-introduce pytest wording** (observed in `archive/2026-09-03-fix-blog-image-urls/tasks.md:20`) → Mitigation: `testing-contract` gate excludes `archive/**` but enforces that new `openspec/changes/*/tasks.md` SHALL NOT contain pytest commands (`pytest`, `python -m pytest`, `pytest -k`) — hard fail via guard lint; allowlist: `openspec/changes/archive/**` only.
- **Guard bypass via branch protection** → Mitigation: `test-contract-guard` is a required status check; PR cannot merge with red gate.
- **CI image without venv/** → Mitigation: fallback chain `venv/bin/pip` → `.venv/bin/pip` → `pip` → `python -m pip` ensures check still runs; missing pip still passes file/import checks.

## Migration Plan

1. Merge `AGENTS.md` + `.gitignore` + specs + CI guard in one PR (no DB migration).
2. Clean local: `rm -rf .pytest_cache conftest.py pytest.ini` (if present).
3. Subsequent PRs: agents copy-pasting `pytest <path>` will get CI red, fix is `venv/bin/python manage.py test <path> --verbosity=2`.
4. Rollback: revert the 4-file change; no stateful side effects.

## Open Questions

- Archive specs (`openspec/changes/archive/2026-08-10-...`) keep pytest language for history — no rewrite needed, but add a note in PR description.

Resolved: `/.venv/` will be added alongside `venv` at `.gitignore:12` (decision: add). Strict Option D removes `Makefile`/`make test` and pre-commit hook — canonical runner remains `venv/bin/python manage.py test` only (no alias).
