## Why

A real Stripe webhook signing secret (`whsec_...`) was committed into a
**public** repository in `docs/stripe-account-setup.md`. GitHub's secret
scanner raised a `stripe_webhook_signing_secret` / "Public leak" alert. Because
the repository is public, the value is exposed in both the current file and in
pushed git history (3 commits), so anyone can read and potentially abuse it to
forge or verify webhook events against the (test-mode) endpoint. Even though the
leaked value is test-mode, public credential exposure is a security incident that
must be remediated: the secret revoked, removed from the working tree, and purged
from git history.

## What Changes

- Remove the literal webhook signing secret from `docs/stripe-account-setup.md`
  and replace it with a non-sensitive placeholder (`whsec_xxxx`), matching the
  pattern already used in `.env.*.example`.
- Purge the leaked string from the **local** git history so the working tree and
  all local commit objects are clean (rewrite via `git filter-branch` fallback;
  `git-filter-repo` was unavailable). This was best-effort hygiene.
- **Final remediation: the GitHub repository was deleted and recreated.** The
  user deleted `darideveloper/enredarte-dashboard` and recreated it, then pushed
  the clean local `main`. This destroyed the old commit objects (SHAs 28ab631,
  98b36c8, d472bad), all forks/PRs of the old repo, and the secret-scanning
  alert in one action — so the residual exposure from the pre-rewrite history is
  gone and the secret is no longer anywhere on GitHub.
- As a result, the originally-planned GitHub Support purge request and the
  "close alert" step are **obsolete** (the objects and alert no longer exist).
- The only remaining action is to **announce to collaborators** to re-clone, so
  anyone with an old clone does not re-introduce the secret by pushing.

## Capabilities

### New Capabilities

- `stripe-secret-remediation`: Requirements for remediating this specific leaked
  webhook signing secret — rotate at Stripe, remove from tree, purge from
  history, close the GitHub alert. (Scoped to this incident, not a permanent
  repo-wide secret policy.)

### Modified Capabilities

<!-- No existing capability requirements change. -->

## Impact

- **Files**: `docs/stripe-account-setup.md` (content edit, placeholder only).
- **Git history (local)**: rewritten via `git filter-branch` to strip the leaked
  string from all local commit objects; verified clean (`git gc --prune=now`).
- **GitHub repository (final fix)**: deleted and recreated. The recreated repo
  received only the clean `main`; the old commit objects, forks, PRs, and the
  secret-scanning alert no longer exist. Re-verified clean via the GitHub API.
- **Stripe account**: rotation/revocation of the affected webhook signing
  secret (operator action, test-mode). Resolved as N/A — API shows **zero
  webhook endpoints**, so the leaked value is a `stripe listen` CLI secret with no
  server-side object to revoke; it is inert once not reused.
- **Collaborators**: anyone who cloned the repo must **re-clone** (or
  `git fetch origin && git reset --hard origin/main`), and must NOT push their old
  local history, which would re-introduce the secret.
- **No application code changes**: the real secret is only ever sourced from the
  gitignored `.env.dev` / deploy secrets (`STRIPE_WEBHOOK_SECRET`), never from
  the docs file, so runtime behavior is unaffected.
