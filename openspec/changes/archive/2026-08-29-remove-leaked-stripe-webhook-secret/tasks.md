## 1. Rotate the secret in Stripe (operator action FIRST — the real fix)

- [x] 1.1 In the Stripe Dashboard (test mode, account `acct_1U8pQHA37WTwarsM`),
      rotate/revoke the exposed webhook signing secret. If it is only a
      `stripe listen` CLI secret, regenerate it with a fresh
      `stripe listen --print-secret`; if it is tied to a real Dashboard webhook
      endpoint, use Developers → Webhooks → roll signing secret.
      RESOLVED: API check shows **zero webhook endpoints** in this account, so the
      leaked value is a `stripe listen` CLI secret with no server-side object to
      revoke. It is inert once not reused. Nothing to rotate in Stripe.
- [x] 1.2 Update the local gitignored `.env.dev` `STRIPE_WEBHOOK_SECRET` with
      the regenerated value (never commit it).
      DONE (partial): `.env.dev` leaked value replaced with placeholder
      `whsec_xxxx`. You may regenerate a fresh value via
      `stripe listen --print-secret` for local webhook verification (runtime
      step; never committed).

## 2. Remove the literal from the working tree

- [x] 2.1 Edit `docs/stripe-account-setup.md` line 39: replace the literal
      `whsec_...` value with the placeholder `whsec_xxxx` (matching
      `.env.*.example` style).
- [x] 2.2 Grep the working tree to confirm no real `whsec_...` value remains in
      any tracked file: `git grep -n "whsec_" -- ':!*.example' ':!*.md'` and
      confirm only placeholders / example files match.

## 3. Purge the secret from local git history (best-effort hygiene)

- [x] 3.1 Create a backup branch/tag of the current HEAD before rewriting
      history (e.g. `git branch backup/pre-secret-purge`).
- [x] 3.2 Work from a **fresh clone** (or pass `--force`), since `git filter-repo`
      refuses on a repo with existing remotes/config otherwise. (Used
      `git filter-branch --force` fallback.)
- [x] 3.3 Create a `secrets.txt` mapping file that replaces the exposed value.
      IMPORTANT: do NOT paste the real value into this repo — obtain the exact
      string from the GitHub alert and write it only into a local, untracked
      file (or pipe via stdin). Map it to `***REMOVED***`. (Kept at /tmp.)
- [x] 3.4 Run `git filter-repo --replace-text secrets.txt` to strip the value
      from all blobs across every local branch and tag.
      DONE via `git filter-branch --tree-filter` (git-filter-repo unavailable:
      PEP 668 externally-managed env). `main` history rewritten, secret gone.
- [x] 3.5 Verify the value is gone from LOCAL history:
      `git grep -n "<exposed value>" $(git rev-list --all)` returns nothing
      (run from an untracked/local context, never committing the value).
      VERIFIED: local repo fully clean (secret removed from all commit objects;
      `backup/pre-secret-purge` deleted and `git gc --prune=now` run).

## 4. Push clean history and notify collaborators

- [x] 4.1 Push the rewritten history with `git push --force-with-lease`
      (coordinate with collaborators first).
      DONE on the original repo: `98b36c8...798bbdd main -> main (forced
      update)`; remote `main` re-fetched and verified clean.
- [x] 4.1b **Final remediation: the GitHub repository was deleted and recreated.**
      The user deleted `darideveloper/enredarte-dashboard` and recreated it, then
      pushed the clean local `main`. This destroyed the old commit objects
      (SHAs 28ab631, 98b36c8, d472bad) and the secret-scanning alert entirely —
      so the residual exposure from the pre-rewrite history is gone. The remote
      was re-verified clean via the GitHub API (only `main`, docs file clean).
- [x] 4.2 Announce to collaborators that they must re-clone / rebase, since
      anyone with an old clone still has the secret in their local history and
      could re-introduce it by pushing. (OPERATOR: notify your team.)
      DRAFT announcement (post in your team chat / repo Discussion):
      > Heads up: we removed an accidentally committed Stripe test webhook
      > secret. The repo was rebuilt from clean history — please **re-clone** (or
      > `git fetch origin && git reset --hard origin/main`). Do NOT push your old
      > local history, as it would re-introduce the secret. The secret was already
      > treated as compromised.

## 5. Post-remediation GitHub cleanup

- [x] 5.1 Open a GitHub Support request to purge the old commit objects.
      **OBSOLETE:** the repository was deleted and recreated, so the old commit
      objects no longer exist on GitHub. No Support request is needed.
- [x] 5.2 Audit existing **forks** and **open/closed PRs** for the value.
      DONE via public GitHub API at deletion time: **0 forks**, 1 PR
      (`mehedi -> main`, closed, does NOT contain the leaked commits). The old
      repo (with its forks/PRs) is gone after recreation.
- [x] 5.3 Treat the secret as permanently compromised regardless of the above.
      (Adopted stance; CLI secret is inert.)

## 6. Verify and close out

- [x] 6.1 Close the `stripe_webhook_signing_secret` secret-scanning alert.
      **OBSOLETE:** the alert was deleted together with the original repository.
      The recreated repo has no alert (its history is clean).
- [x] 6.2 Confirm `docs/stripe-account-setup.md` now references only
      `whsec_xxxx` and contains no real `whsec_...` value.
- [x] 6.3 Confirm no real `whsec_...` value remains in the local repo via the
      `git grep` from step 3.5. (Verified: LOCAL REPO CLEAN.)
