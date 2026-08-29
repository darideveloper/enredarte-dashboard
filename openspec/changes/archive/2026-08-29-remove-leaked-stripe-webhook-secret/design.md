## Context

The Enredarte dashboard is a public GitHub repository. During the subscriptions
work, the output of `stripe listen --print-secret` (a Stripe webhook signing
secret, `whsec_...`) was pasted literally into `docs/stripe-account-setup.md`
as documentation. GitHub secret scanning detected the leak.

Investigation confirmed:
- The literal value exists only in `docs/stripe-account-setup.md` (line 39).
- It is present in 3 pushed commits (`d472bad`, `28ab631`, `98b36c8`), so it is
  in public history, not just the working tree.
- `.env.dev` is gitignored; only `.env.*.example` are tracked. The example files
  already use the placeholder `whsec_xxxx`.
- The application reads the real secret from `STRIPE_WEBHOOK_SECRET` (gitignored
  `.env` / deploy secrets), never from the docs file, so runtime behavior does
  not depend on the doc.

This is a test-mode secret, but public exposure is treated as a real incident:
the value must be revoked, removed from the tree, and purged from history.

## Goals / Non-Goals

**Goals:**
- Revoke/rotate the exposed webhook signing secret in Stripe.
- Remove the literal value from the working file, replacing it with a placeholder.
- Purge the value from all git history (public repo) and force-push.
- Close the GitHub alert as "revoked".

**Non-Goals:**
- No application code changes (no models, views, settings, or migrations).
- No change to how the app loads `STRIPE_WEBHOOK_SECRET`.
- No rotation of the Stripe API keys or price IDs (not leaked).
- No change to the subscriptions feature behavior.

## Decisions

1. **Placeholder instead of real value in docs.**
   Replace the literal with `whsec_xxxx` (consistent with `.env.*.example`).
   Rationale: docs should describe *how* to obtain the secret, never embed it.

 2. **Full history rewrite (local history only).**
    Because the repo is public, a normal commit only removes the value from the
    latest tree — it remains readable in the 3 historical commits. The preferred
    tool is `git filter-repo --replace-text`, which strips the string from every
    blob across **all local refs** (every branch and tag). Alternative considered:
    `git rebase` + amend (manual, error-prone for multiple commits) and BFG
    (similar result, extra tooling). `git filter-repo` is the modern, maintained
    standard and ships with Git on most platforms.

    **What was actually executed:** `git-filter-repo` was **unavailable** in the
    execution environment (PEP 668 externally-managed Python — `pip install`
    refused without `--break-system-packages`). As the documented fallback, the
    rewrite was performed with `git filter-branch --force --tree-filter 'sed -i
    "s#<exposed>#***REMOVED***#g" docs/stripe-account-setup.md' -- main`. The
    result is equivalent: `main` and `origin/main` were both verified clean of
    the secret. (The secret string was sourced from a local, untracked
    `/tmp` mapping file, never from or into the repo.)

    **Caveat — this is best-effort, not a security guarantee.** A history
    rewrite only cleans the *local* repository and whatever the force-push
    overwrites on the default branch. It does **not** remove the value from:
    GitHub's retained server-side commit objects (still fetchable by SHA at
    `https://github.com/.../commit/<sha>` and via API), existing **forks**, or
    **pull requests** that referenced those commits. The value must therefore be
    treated as permanently exposed the instant it was public — which is why
    **rotation in Stripe (Step 1) is the actual remediation**, and the history
    purge is hygiene.

3. **Operator revokes the secret BEFORE the code fix lands.**
   The secret is compromised the moment it is public; rotation is the first
   action, independent of the repo edit. For a `stripe listen` secret this means
   regenerating via a fresh `stripe listen --print-secret`; for any real
   Dashboard webhook endpoint it means rolling the signing secret in the
   Dashboard and updating local `.env.dev`.

4. **Force-push is required and expected.**
   Rewriting public history requires `git push --force-with-lease`. All
   collaborators must re-clone/rebase afterward.

## Risks / Trade-offs

- **[History rewrite disrupts collaborators]** → Coordinate: announce the
  force-push, then ask everyone to re-clone. Use `--force-with-lease` to avoid
  clobbering unrelated pushes.
- **[Secrets persist in GitHub's server copy, forks, and PRs]** → A local
  `filter-repo` + force-push does **not** clear GitHub's retained commit
  objects (still reachable by SHA), any pre-existing forks, or PRs that touched
  the commits. Mitigations: (a) rotate the secret FIRST so any residual copy is
  useless; (b) after force-push, open a GitHub Support request to purge the old
  commit objects / cached views; (c) audit forks and open/closed PRs for the
  value; (d) treat the secret as permanently compromised regardless.
  **RESOLVED IN PRACTICE:** the chosen remediation was to **delete and recreate
  the GitHub repository**, which destroyed the old commit objects, all forks/PRs
  of the old repo, and the secret-scanning alert in one action. Steps (b) and
  (c) therefore became unnecessary.
- **[filter-repo refuses on a configured repo]** → `git filter-repo` errors
  unless run from a fresh clone or with `--force`. Run it on a clean clone (or
  pass `--force`) to avoid the "not a fresh clone" refusal.
- **[Accidental re-leak during fix]** → Never paste the real value into commit
  messages, the proposal, design, or tasks. Use `whsec_xxxx` placeholders only.
- **[filter-repo missing]** → Fall back to BFG or manual rebase; verify the
  string is gone with `git grep` across all refs before pushing.

## Migration Plan

1. **Operator: rotate/revoke the webhook signing secret in Stripe (test mode).**
   This is the real remediation — once rotated, any copy of the old value still
   floating in history/forks/PRs is useless.
2. Edit `docs/stripe-account-setup.md` → replace literal with `whsec_xxxx`.
3. On a **fresh clone** (or with `--force`), run the history rewrite to purge
   the local history across all refs. Preferred:
   `git filter-repo --replace-text secrets.txt` (secrets.txt maps the leaked
   string → `***REMOVED***`). If `git-filter-repo` is unavailable (e.g. PEP 668
   externally-managed Python), use the equivalent fallback:
   `git filter-branch --force --tree-filter 'sed -i "s#<exposed>#***REMOVED***#g" docs/stripe-account-setup.md' -- main`.
4. Verify locally: `git grep -n "<exposed value>" $(git rev-list --all)` returns
   nothing (run from an untracked/local context — never commit the value).
 5. `git push --force-with-lease` to overwrite the default branch history of the
    original repo.
 6. **Final remediation (actual): the GitHub repository was deleted and recreated.**
    The user deleted `darideveloper/enredarte-dashboard` and recreated it, then
    pushed the clean local `main`. This eliminated the old commit objects
    (SHAs 28ab631, 98b36c8, d472bad), all forks/PRs of the old repo, and the
    secret-scanning alert. The remote was re-verified clean via the GitHub API.
    - Open a GitHub Support request to purge old commit objects → **OBSOLETE**
      (objects destroyed by repo deletion).
    - Audit forks/PRs → **DONE** at deletion time (0 forks; only a closed,
      clean PR existed).
 7. Close the GitHub secret alert as "revoked" → **OBSOLETE** (alert deleted with
    the original repository; the recreated repo has none).
 8. **Announce to collaborators to re-clone** (the only remaining action — see
    tasks 4.2). Anyone with an old clone still has the secret locally and could
    re-introduce it by pushing.

Rollback: the pre-rewrite state was recoverable from the local reflog / backup
branch; however the repository was ultimately rebuilt from clean history, so
rollback is no longer relevant.

## Open Questions

- *Resolved:* Does any collaborator have an unpublished branch containing the
  secret? Verified at deletion: 0 forks and only a closed, clean PR existed, and
  the recreated repo received only the clean `main`. No re-introduction observed.
- *Resolved:* Is there a Stripe Dashboard webhook endpoint tied to this secret?
  No — `GET /v1/webhook_endpoints` returned zero endpoints, so the leaked value
  is a `stripe listen` CLI secret with no server-side object to revoke.
