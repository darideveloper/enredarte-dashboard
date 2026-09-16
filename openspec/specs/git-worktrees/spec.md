# git-worktrees

## Purpose
To define the sibling git-worktree workflow: one runnable checkout per branch with its own portless domain, per-sibling venv/env/migrate/openspec bootstrap, shared-database discipline, and a one-command merge-and-cleanup finish flow (pattern mirrors the clients project).

## Requirements

### Requirement: Sibling worktree layout and creation

The system SHALL support one runnable checkout per branch as a sibling directory sharing one `.git`, created with `worktree-new.sh`, never nested inside the main checkout and never via the `worktree_create` / `worktree_delete` plugin tools.

#### Scenario: Create sibling for a new branch

- **WHEN** the agent runs `./worktree-new.sh ../enredarte-dashboard-feature feature/xyz main` from a clean main checkout
- **THEN** a sibling worktree exists at `../enredarte-dashboard-feature` on branch `feature/xyz` based on `main`, and `git worktree list` shows both checkouts

#### Scenario: Rejected creation modes

- **WHEN** the agent is asked to isolate a branch
- **THEN** it does not nest the worktree inside the main checkout and does not use plugin worktree tools

### Requirement: Per-sibling bootstrap (venv, env, migrate)

The system SHALL bootstrap every sibling with a fresh `venv` plus installed dependencies, copied environment files, and applied migrations, so the checkout runs without further setup.

#### Scenario: Fresh sibling boots runnable

- **WHEN** `worktree-new.sh` finishes for a new sibling
- **THEN** the sibling contains `venv/bin/python` with `requirements.txt` installed, `.env` and `.env.dev` (plus `.env.prod` when main has it) copied from the main checkout, and migrations applied against the shared database

#### Scenario: Venv is never shared

- **WHEN** the bootstrap sets up Python
- **THEN** it creates a new virtualenv in the sibling instead of symlinking the main checkout's `venv`

### Requirement: Per-sibling dev server identity

The system SHALL give each sibling its own runnable identity derived from its directory basename: its own portless `.localhost` URL, its own tmux session, and a non-colliding port.

#### Scenario: Two checkouts run side by side

- **WHEN** main and a sibling each run `./dev.sh`
- **THEN** each serves on its own portless domain and tmux session, and `portless list` shows both routes

#### Scenario: Portless-injected port is respected

- **WHEN** `dev.sh` starts under portless with `$PORT` set
- **THEN** it uses the injected port instead of always starting at 8000

### Requirement: Sibling settings resolve without edits

The system SHALL resolve a copied `.env.dev` in any sibling without manual edits: `HOST` prefers `PORTLESS_URL`, and in `DEBUG` the checkout's own dev host is accepted for HTTP, CORS, and CSRF.

#### Scenario: Copied env works in sibling

- **WHEN** a sibling boots with main's copied `.env.dev` under portless
- **THEN** requests to the sibling's own `.localhost` domain do not raise `DisallowedHost` and pass CORS/CSRF host checks

### Requirement: Openspec works in every sibling

The system SHALL sync the openspec agent workflow into each new sibling while keeping active proposals isolated per sibling.

#### Scenario: New sibling has the workflow

- **WHEN** `worktree-new.sh` finishes
- **THEN** the sibling contains `.opencode/skills/openspec-*` and `.opencode/commands/opsx-*.md` copied from the main checkout

#### Scenario: Active proposals stay isolated

- **WHEN** work happens in a sibling under `openspec/changes/*`
- **THEN** it does not appear in the main checkout until the finish flow copies back only `openspec/changes/archive/`

### Requirement: Finish flow merges and cleans up

The system SHALL finish a sibling with `worktree-done.sh`: copy back `archive/`, require committed trees, merge the sibling branch with `git merge --no-ff`, and only after a successful merge plus migrations stop the sibling server and remove the worktree, prune, and delete the branch.

#### Scenario: Clean finish

- **WHEN** the agent runs `./worktree-done.sh ../enredarte-dashboard-feature main` with the sibling fully committed and main tracked-clean
- **THEN** the sibling branch is merged into `main` keeping both sides' history, migrations run clean, and the sibling directory, worktree registration, and branch no longer exist

#### Scenario: Conflict stops without cleanup

- **WHEN** the merge conflicts or the post-merge migration fails
- **THEN** the script exits without resolving anything or deleting anything, lists the conflicted files, and a re-run after manual resolution resumes and completes the merge and cleanup

### Requirement: Shared database discipline

The system SHALL document that all siblings share Postgres `DB_NAME=enredarte`, migrations run from one sibling at a time, tests stay sqlite-isolated, and a per-sibling sqlite escape hatch exists.

#### Scenario: Escape hatch documented

- **WHEN** a developer needs full DB isolation in a sibling
- **THEN** the runbook shows setting `DB_ENGINE=django.db.backends.sqlite3` in that sibling's `.env.dev`

### Requirement: Agent worktree contract

The system SHALL constrain agents to the manual sibling lifecycle: clean-tree pre-flight, `worktree-new.sh` / `dev.sh` / `worktree-done.sh` commands, no auto-started servers, and no removal of siblings with unmerged or unreviewed work.

#### Scenario: Agent follows the runbook

- **WHEN** the user asks for branch isolation
- **THEN** the agent checks `git status` first, uses the scripts in order, verifies with `portless list`, and asks before resolving any merge conflict
