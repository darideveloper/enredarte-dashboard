## 1. Runtime enablers (settings + dev server)

- [x] 1.1 Fix `project/settings.py` HOST/ALLOWED_HOSTS: add `urlparse` import, strip `ALLOWED_HOSTS` entries, resolve `HOST` from `PORTLESS_URL` first (mirror `clients/project/settings.py:4,28-32`)
- [x] 1.2 Add DEBUG sibling-host block in `project/settings.py` after the CSRF section (mirror `clients/project/settings.py:174-185`): append checkout's own `.localhost` host to `ALLOWED_HOSTS`, CORS, CSRF
- [x] 1.3 Fix `dev.sh` port line: `PORT=8000` → `PORT=${PORT:-8000}` so portless-injected `$PORT` is respected
- [x] 1.4 Run `venv/bin/python manage.py check` and `venv/bin/python manage.py test --verbosity=1` on main to confirm no regression

## 2. Worktree scripts

- [x] 2.1 Add `worktree-new.sh` (port `clients/worktree-new.sh:1-54`; adapt env fallbacks to `.env.dev.example` / `.env.prod.example`, copy `.env` + `.env.dev` + `.env.prod` when present; keep fresh venv + pip install, migrate, openspec `cp -rn` sync) and `chmod +x`
- [x] 2.2 Add `worktree-done.sh` (port `clients/worktree-done.sh:1-88` unchanged: archive copyback, clean-tree guards, `merge --no-ff` with stop-and-ask + `MERGE_HEAD` resume, migrate, kill tmux session, remove/prune/`branch -d`) and `chmod +x`
- [x] 2.3 Shell-check both scripts (`bash -n worktree-new.sh worktree-done.sh`) and verify usage errors (`./worktree-new.sh` with no args prints usage)

## 3. Runbook and agent contract

- [x] 3.1 Add `docs/django-worktrees.md` (port `clients/docs/django-worktrees.md:1-145`; rename paths/URLs to `enredarte-dashboard`, `DB_NAME=enredarte`, example files to `.env.dev.example`/`.env.prod.example`; add tunnel-main-only rule and `bruno/.../dev.bru` row to the what-doesn't-transfer table)
- [x] 3.2 Add `AGENTS.md ## Git Worktrees` section (mirror `clients/AGENTS.md:13-32` with `../enredarte-dashboard-<branch>` layout, lifecycle, bootstrap, shared-DB + sqlite hatch, archive-only sharing, never-autostart rule)

## 4. End-to-end verification on a throwaway sibling

- [x] 4.1 Pre-flight `git status --short --branch` clean, then `./worktree-new.sh ../enredarte-dashboard-wt-test wt-test main` and confirm `git worktree list` shows both checkouts
- [x] 4.2 In the sibling verify bootstrap: `venv/bin/python` exists with deps installed, `.env` + `.env.dev` present, `.opencode/skills/openspec-*` and `.opencode/commands/opsx-*.md` present, `venv/bin/python manage.py check` and `migrate --noinput` pass
- [x] 4.3 Boot sibling `./dev.sh`, confirm per-sibling domain via `portless list`, then stop the server (`tmux kill-session -t enredarte-dashboard-wt-test_dev`)
- [x] 4.4 Finish with `./worktree-done.sh ../enredarte-dashboard-wt-test main`, confirm merge kept both sides, `git worktree list` clean, branch deleted, and run `./.opencode/commands/guard.sh` plus `venv/bin/python manage.py test --verbosity=1` on main

## 5. Verification follow-ups

- [x] 5.1 Record executable bit in git (`git update-index --chmod=+x` on both scripts; committed as `2a9b0be`)
- [x] 5.2 Add `worktree-scripts-syntax` CI job (`bash -n` on both scripts + committed-mode assertion)
- [x] 5.3 Live conflict drill on scratch branches (conflict → stop with files listed, nothing cleaned → resolve → re-run resumes via `MERGE_HEAD`, merge commit keeps both sides, full cleanup; scratch branches deleted, main history untouched)
