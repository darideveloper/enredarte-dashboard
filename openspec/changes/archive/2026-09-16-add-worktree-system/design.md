## Context

`clients` (`/mnt/hd/develop/django/clients`) runs a proven sibling-worktree loop: `worktree-new.sh` / `worktree-done.sh` at root, `docs/django-worktrees.md` runbook, `AGENTS.md ## Git Worktrees` contract, plus two enablers — `project/settings.py` resolves `HOST` from `PORTLESS_URL` and auto-accepts the checkout's own `.localhost` domain in DEBUG (`settings.py:30-32,174-185`), and `dev.sh:19` respects portless-injected `$PORT`.

Enredarte-dashboard has none of the four framework pieces and both enablers are broken: `project/settings.py:18-19` ignores `PORTLESS_URL` and never appends the sibling host (→ `DisallowedHost` in any sibling), and `dev.sh:15` hardcodes `PORT=8000` (→ second checkout collides). Its `.env` model also differs (`.env` selector + `.env.dev` / `.env.prod` + examples vs clients' `.env.example` fallback), and its `dev.sh` carries an extra Cloudflare tunnel window sharing one `CLOUDFLARE_TUNNEL_HOST` across checkouts.

Constraints: additive change only (no prod/deploy behavior change); `docs/` is tracked here so no gitignore exception is needed (unlike clients); `.*/` ignores `.opencode/` and `openspec/changes/*` ignores active proposals in both repos, so the filesystem `cp -rn` sync / `archive/`-only copyback pattern transfers unchanged; shared Postgres `DB_NAME=enredarte` stays the project decision with tests forced to sqlite (`settings.py:94-101`).

## Goals / Non-Goals

**Goals:**
- One checkout per branch, all runnable at once via portless basename URLs (`enredarte-dashboard` → its domain, `enredarte-dashboard-<branch>` → its domain), mirroring `clients`.
- Every sibling boots fully working: fresh `venv` with installed deps, copied env, migrated DB, synced openspec skills/commands.
- One-command finish: merge keeping both sides, stop-and-ask on conflict/migration failure, full cleanup afterwards.
- Agent contract so a "create a worktree" request follows the runbook without improvisation.

**Non-Goals:**
- No per-sibling database auto-provisioning (shared Postgres stays; sqlite hatch documented).
- No `opencode.json`, `.gitignore`, CI, or Docker/prod changes.
- No squash/rebase flows, no nested worktrees, no `worktree_create` / `worktree_delete` plugin tools.
- No auto-starting dev servers from agents.

## Decisions

- **Port `clients` scripts verbatim, adapt only env fallbacks.** `worktree-new.sh` bootstrap order (worktree add → venv+pip → env copy → migrate → openspec sync) and `worktree-done.sh` order (archive copyback → clean-tree guards → `--no-ff` merge → migrate → remove/prune/`branch -d`) are proven. Alternative (rewrite from scratch) rejected: needless divergence risk. Only change: enredarte `.env.example` holds just the `ENV=dev` selector, so the `.env.dev` fallback becomes `.env.dev.example`, plus copy `.env.prod` (fallback `.env.prod.example`).
- **Sibling layout `../enredarte-dashboard-<branch>`, same session, never nested.** Keeps `dev.sh`'s `PROJECT_NAME=$(basename "$PWD")` URL/session model working and avoids git nesting errors. Rejected plugin tools: they nest under a central store and open a new terminal, breaking the basename-URL convention (`clients` runbook documents this).
- **Fresh `venv` per sibling, never symlink.** Isolation: different branches may pin different deps; a symlinked venv breaks when main's interpreter/deps change. Cost (~1 `pip install`) accepted; it delivers the "venv with modules already installed" goal explicitly.
- **Copy env files from main; copied `HOST` is harmless.** Settings resolve `PORTLESS_URL → HOST → fallback` (after fix) and DEBUG appends the checkout's own host, so a stale `HOST` never blocks a sibling. Rejected alternative (regenerating env from examples): would lose real secrets/tokens the developer already configured.
- **Shared Postgres + sqlite escape hatch.** Matches `clients` and current enredarte settings; per-sibling databases would require provisioning automation out of scope. Mitigated by "migrate from one sibling at a time" rule.
- **Openspec via markdown sync + `archive/`-only copyback.** `.opencode/skills/openspec-*` + `commands/opsx-*.md` are untracked dotfolders (identical in both repos, verified on disk); `cp -rn` gives each sibling a working workflow, while active proposals stay isolated and only finished `archive/` travels back at merge.
- **Keep Cloudflare tunnel block, document as main-only.** Removing it would regress prod-like tunnel testing; running the same `CLOUDFLARE_TUNNEL_HOST` from two checkouts collides, so the runbook declares the tunnel a main-checkout activity.
- **Merge `--no-ff`, stop-and-ask, re-runnable resume.** Keeps both sides' history (no squash loss), never auto-resolves conflicts, detects in-progress `MERGE_HEAD` to resume after the user fixes conflicts — same semantics as `clients/worktree-done.sh:44-69`.

## Risks / Trade-offs

- [Shared-DB concurrent migrate] → Rule: migrate from one sibling at a time; sqlite hatch (`DB_ENGINE=django.db.backends.sqlite3` in sibling `.env.dev`) for full isolation.
- [Sibling starts from HEAD without uncommitted changes] → `worktree-new.sh` warns when main is dirty; runbook requires commit/stash first.
- [Tunnel hostname collision] → Runbook: tunnel runs from main only; siblings use portless `.localhost` URLs.
- [`worktree remove` fails while server holds the dir] → Runbook + script order: stop sibling dev server first (`tmux kill-session -t <basename>_dev`); script surfaces the failure without deleting anything.
- [Branch names with `/`] → Sanitized in the portless domain; runbook tells the agent to confirm via `portless list`.
- [Bruno `dev.bru` doesn't transfer] → Same class as `.env`: gitignored secret file; runbook lists re-creating it from `.bru.example` as a manual sibling step.

## Migration Plan

Additive, no deployment: add two scripts + one doc, append one `AGENTS.md` section, apply two small edits (`settings.py`, `dev.sh`). Verify on a throwaway branch (`wt-test` create → check/migrate/test → `dev.sh` + `portless list` → finish/merge → worktree list clean). Rollback: delete the three added files and revert the two edits; no data migration involved.

## Resolved Decisions (locked)

- Sibling prefix is `../enredarte-dashboard-<branch>` (direct analog of clients' `../clients-<branch>`, matching the `dev.sh` basename URL/session model).
- Cloudflare tunnel runs from the main checkout only (per-sibling tunnel hostnames are out of scope).
