# Project Conventions

## Django models — always populate admin-visible texts

Every time a Django model is created or edited, the following MUST be present
(`verbose_name`, `help_text` and `__str__` are visible in the Django Admin and
are never optional):

1. `Meta.verbose_name` and `Meta.verbose_name_plural` on every model.
2. `verbose_name` on every field.
3. `help_text` on non-obvious fields.
4. A content-based `__str__` (never Django's default `"Model object (N)"`).
5. Join / M2M-through models and translation rows also get a content-based
   `__str__`; translation rows return `"{parent} ({language})"`.

Language: **English by default**. Write Spanish literals instead if the project
follows `docs/django-i18n-es-admin.md` (Spanish Django Admin).

For translated models whose display name lives in `*Translation` rows, use the
`TranslatableName` mixin (`translated_name()` / `translated_title()`, es-first
→ any translation → slug).

Full reference: `docs/django-model-definitions.md`.

## Git Worktrees

One checkout per branch, all runnable at once (`main` → `https://enredarte-dashboard.localhost`,
sibling `../enredarte-dashboard-<branch>` → `https://enredarte-dashboard-<branch>.localhost`).
Full runbook: `docs/django-worktrees.md`.

- Manual siblings only, same session. Never `worktree_create` / `worktree_delete`
  plugin tools; never nest a worktree inside the main checkout.
- Lifecycle: `git status` clean first, then `./worktree-new.sh ../enredarte-dashboard-<branch> [branch] [base]`,
  `cd` in, `./dev.sh`. Stop the dev server before `git worktree remove`; `prune` after.
- Finish: `./worktree-done.sh ../enredarte-dashboard-<branch> [into]` merges keeping both sides
  (`--no-ff`), stops + asks on any conflict (never auto-resolve), then full cleanup
  (stop server, remove, prune, `branch -d`). Sibling must be fully committed clean,
  main tracked-clean first.
- Bootstrap per sibling is fresh `venv` + `pip install` (never symlink), `.env` copy
  (harmless — settings resolve `PORTLESS_URL → HOST`), `migrate`, openspec skills sync.
- Gotchas: shared Postgres `enredarte` DB (migrate from one sibling at a time;
  `DB_ENGINE=django.db.backends.sqlite3` escape hatch); openspec active proposals stay
  isolated (only `archive/` shared back); Cloudflare tunnel runs from main only;
  agents never autostart servers (verify with `portless list`).

## Testing — Django only

Canonical runner: `venv/bin/python manage.py test [--verbosity=2]` (or `python manage.py test` when venv is active). Use Django test labels for targeted runs, e.g. `venv/bin/python manage.py test subscriptions.tests.AdminEndpointTest.test_sync_from_stripe_reconciles_state --verbosity=2` — do not use pytest nodeids (`-k`).

Allowed bases/helpers: `django.test.TestCase`, `rest_framework.test.APITestCase` / `APIClient`, `django.test.RequestFactory`, `django.test.override_settings`, `django.core.files.uploadedfile.SimpleUploadedFile`, `django.core.management.call_command`, and stdlib helpers (`unittest.mock`, `base64`, `hashlib`, `hmac`, `Decimal`, `json`). Only testing extra in `requirements.txt:18` is `selenium`.

**Banned:** `pytest`, `pytest-django`, `conftest.py`, `pytest.ini`/`.pytest.ini`, `setup.cfg` with `[tool:pytest]`, `pyproject.toml` with `[tool.pytest]` / `[tool.pytest.ini_options]`, and any `import pytest` / `from pytest` / `@pytest.*` in `*.py`. Do not add `conftest.py`, `pytest.ini`, or pytest config. The contract is enforced by `.opencode/commands/guard.sh` and CI job `test-contract-guard` (see `openspec/specs/testing-contract/spec.md`). References: `project/settings.py:88` (`IS_TESTING`) and `project/settings.py:203-214` (StaticFilesStorage fallback).
