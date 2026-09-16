## Why

Parallel branches in a single checkout allow only one dev server at a time and force stash/checkout cycles. The `clients` project already solved this with a sibling-worktree system (one checkout per branch, each runnable with its own `.localhost` URL, venv, and openspec workflow); enredarte-dashboard has none of it and siblings would break (`DisallowedHost`, fixed port 8000).

## What Changes

- Add `worktree-new.sh` at repo root: creates a sibling worktree (`../enredarte-dashboard-<branch>`), fresh `venv` + `pip install -r requirements.txt`, copies `.env` / `.env.dev` / `.env.prod` from main, runs `migrate`, syncs `.opencode` openspec skills/commands.
- Add `worktree-done.sh` at repo root: copies back `openspec/changes/archive/`, requires clean trees, merges sibling branch with `git merge --no-ff` (stop-and-ask on conflict or failed migration, re-runnable), then stops the sibling dev server, `worktree remove`, `prune`, `branch -d`.
- Add `docs/django-worktrees.md` runbook: URL model, layout, lifecycle, finish flow, what-doesn't-transfer table (venv, env, sqlite, media/staticfiles, `dev.bru`, dotfolders), shared-Postgres DB + sqlite escape hatch, openspec isolation, stopping, troubleshooting (incl. Cloudflare tunnel collision).
- Add `AGENTS.md ## Git Worktrees` agent contract: manual siblings only in the same session, never `worktree_create` / `worktree_delete` plugin tools, never nested worktrees, lifecycle commands, bootstrap and gotchas, agents never autostart servers.
- Fix `project/settings.py`: resolve `HOST` from `PORTLESS_URL` first, strip `ALLOWED_HOSTS` entries, auto-accept the checkout's own dev `.localhost` host into `ALLOWED_HOSTS` / CORS / CSRF when `DEBUG`.
- Fix `dev.sh`: respect portless-injected `$PORT` (`PORT=${PORT:-8000}`); keep the Cloudflare tunnel window but document it as main-only.

## Capabilities

### New Capabilities

- `git-worktrees`: sibling worktree lifecycle (create, bootstrap, run, finish/merge/cleanup), per-sibling venv + env + migrate + openspec sync, shared-DB and isolation rules, agent constraints.

### Modified Capabilities

- None (no existing spec's REQUIREMENTS change; settings/dev.sh edits are implementation of the new capability).

## Impact

- New files: `worktree-new.sh`, `worktree-done.sh`, `docs/django-worktrees.md` (tracked; `docs/` is not gitignored here).
- Edited: `AGENTS.md` (new section), `project/settings.py` (HOST/ALLOWED_HOSTS/CORS/CSRF dev handling + `urlparse` import), `dev.sh` (PORT line).
- No dependency, API, migration, or prod-deploy changes. Shared Postgres `DB_NAME=enredarte` stays the project decision; tests remain forced-sqlite isolated.
