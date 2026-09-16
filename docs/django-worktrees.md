# Git Worktrees + Portless (Django)

One checkout per branch, all runnable at once. Each sibling gets its own
stable `.localhost` URL automatically — no port juggling, no stash/checkout
cycles. Pattern mirrors `docs/django-worktrees.md` in the clients project.

## Why

Parallel branches share a single checkout by default, allowing only one dev
server at a time. Git worktrees give every branch its own directory sharing
one `.git`, and `dev.sh` (tmux + portless) gives every directory its own
domain: `main` and any number of branches run side by side.

## Prerequisites

- git, tmux, portless (`npm install -g portless`), Python 3.12, local Postgres
  (or `DB_ENGINE=django.db.backends.sqlite3` in `.env.dev` to bypass it).

## URL model

`dev.sh` derives everything from the directory basename:

```
main checkout (dir `enredarte-dashboard`):          https://enredarte-dashboard.localhost
sibling (dir `enredarte-dashboard-<branch>`):       https://enredarte-dashboard-<branch>.localhost
```

Each sibling also gets its own tmux session (`<basename>_dev`) and its own
port (portless-injected `$PORT` first, else auto-scanned from 8000).
`portless list` is the source of truth for live routes.

## Layout

Siblings only, in the same session. Never nest a worktree inside the main
checkout. Never use the `worktree_create` / `worktree_delete` plugin tools
(they open a new terminal and nest under a central store).

```bash
/mnt/hd/develop/django/
  enredarte-dashboard/              # main checkout
  enredarte-dashboard-<branch>/     # sibling worktree (e.g. enredarte-dashboard-feature-auth)
```

## Lifecycle

Pre-flight in main: `git status --short --branch`. Commit or stash first —
siblings start from committed `HEAD` only.

```bash
git fetch origin
./worktree-new.sh ../enredarte-dashboard-<branch> <branch>            # existing branch
./worktree-new.sh ../enredarte-dashboard-feature feature/xyz main     # new branch
git worktree list
cd ../enredarte-dashboard-<branch> && ./dev.sh   # -> https://enredarte-dashboard-<branch>.localhost
# ... after merge, stop the dev server first, then:
git worktree remove ../enredarte-dashboard-<branch>
git worktree prune
```

`worktree-new.sh` performs the full bootstrap per sibling: fresh `venv`,
`pip install -r requirements.txt`, `.env`/`.env.dev`/`.env.prod` copy (from
main, else `.env.dev.example`), `migrate`, and `.opencode` openspec
skills/commands sync.

## Finish (merge + delete)

When the sibling's work is done and committed, the agent merges it back with
`worktree-done.sh` — one command, same session:

```bash
./worktree-done.sh ../enredarte-dashboard-<branch>            # into current branch
./worktree-done.sh ../enredarte-dashboard-<branch> main       # into main explicitly
```

What it does, in order:

1. Copies the sibling's `openspec/changes/archive/` back (active proposals
   are gitignored and never cross on their own).
2. Refuses to start unless work is committed: the sibling fully clean
   (untracked included — everything must travel via the branch), main
   tracked-clean. Commit or stash first on both sides.
3. Merges the sibling branch with `git merge --no-ff` (keeps every commit
   from both sides; no squash, no rebasing).
4. **On any conflict or failed migration it stops**: nothing is resolved,
   nothing is deleted. It lists the conflicted files (merge stays open) and
   the agent asks you how to proceed. Fix, then re-run the same command to
   resume — it completes the merge and continues cleanup.
5. Only after a correct merge: stops the sibling dev server, `worktree
   remove`, `prune`, and `branch -d` (`-d` still refuses if anything ended
   up unmerged).

Never `worktree remove` a sibling with unmerged/unreviewed work, and never
resolve a conflicted merge without being asked.

## What doesn't transfer

| Path | Why | Action per sibling |
|---|---|---|
| `venv/` | gitignored | fresh `python3 -m venv venv` + `pip install` (never symlink) |
| `.env`, `.env.dev`, `.env.prod` | gitignored (secrets) | copied by `worktree-new.sh` |
| `db.sqlite3`, `testing.sqlite3` | gitignored | recreated; tests always use sqlite |
| `media/`, `staticfiles/` | gitignored | recreated |
| `bruno/collections/*/environments/dev.bru` | gitignored (real tokens) | re-create from `dev.bru.example` and fill the token |
| Dotfolders (`.opencode/`, …) | gitignored via `.*/` | openspec skills/commands synced by script |
| Uncommitted changes | siblings start from `HEAD` | commit or stash first |

A copied `.env.dev` keeps main's `HOST` — harmless: settings resolve
`PORTLESS_URL → HOST → fallback` and accept the checkout's own `.localhost`
domain in dev.

## Database

All siblings share Postgres `DB_NAME=enredarte` (project decision). Migrate
from one sibling at a time; test runs are isolated (forced sqlite).
Escape hatch for full isolation:

```bash
# in the sibling's .env.dev:
DB_ENGINE=django.db.backends.sqlite3
```

## Openspec per sibling

Active proposals under `openspec/changes/*` stay isolated per sibling (only
`openspec/changes/archive/` is tracked). New siblings get the workflow via
the `.opencode/skills/openspec-*` + `commands/opsx-*.md` markdown sync in
`worktree-new.sh`. Before merge, copy back only `archive/`.

## Cloudflare tunnel (main checkout only)

`dev.sh` also opens a Cloudflare tunnel window from `CLOUDFLARE_TUNNEL_NAME` /
`CLOUDFLARE_TUNNEL_HOST` in `.env.dev`. The tunnel hostname is shared, so
running `./dev.sh` in two checkouts at once collides — run the tunnel from
the main checkout only; siblings use their portless `.localhost` URLs.

## Stopping

- One dev server per checkout: detach or `tmux kill-session -t <name>_dev`.
- There is **no per-route stop command** (`portless stop <name>` registers a
  bogus route). The route unregisters when its dev process exits.
- Deleting a worktree does **not** stop its server — stop it first.
- Agents never autostart servers; start `./dev.sh` manually and confirm with
  `portless list`.

## Troubleshooting

| Issue | Fix |
|---|---|
| `DisallowedHost` in a sibling | Pull latest `main` (URL chain lives in `settings.py`), restart `./dev.sh` |
| Second `./dev.sh` attaches unexpectedly | Session `<basename>_dev` already exists — attach is intended; kill it to restart |
| Proxy 404 but direct `http://127.0.0.1:<port>/` answers | Parent process died, route unregistered — restart `./dev.sh` |
| Killed the parent but the port is still bound | `kill` on the portless parent orphans the `runserver` child — kill the child `venv/bin/python manage.py runserver <port>` too, then remove |
| `.localhost` doesn't resolve (Safari, Firefox) | `portless hosts sync` |
| Tunnel hostname already in use | Another checkout runs the tunnel — keep it on main only (see above) |
| Branch names with `/` | Sanitized in the domain — check `portless list` after first boot |
