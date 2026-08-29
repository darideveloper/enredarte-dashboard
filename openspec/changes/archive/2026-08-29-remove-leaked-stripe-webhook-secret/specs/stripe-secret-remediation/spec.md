## ADDED Requirements

### Requirement: System MUST rotate the exposed webhook signing secret at Stripe
The team SHALL rotate or revoke the exposed webhook signing secret in Stripe
(test mode) before any repository change is made.
When a real Stripe webhook signing secret is found committed in the public
repository, this rotation is performed first.

#### Scenario: Secret detected in public repo
- **WHEN** a real `whsec_...` webhook signing secret is present in a tracked file
      or in git history of the public repo
- **THEN** the secret is rotated/revoked in the Stripe Dashboard (or regenerated
      via `stripe listen`) before editing the repository

#### Scenario: No server-side object exists to rotate
- **WHEN** the leaked secret is a `stripe listen` CLI secret and the Stripe
      account has **zero** webhook endpoints (verified via `GET /v1/webhook_endpoints`)
- **THEN** there is no Dashboard secret to roll; the value is inert once not
      reused, and the history scrub (Requirement 2) is the effective remediation.
      This is recorded as a no-op resolution, not a gap.

### Requirement: Leaked secret MUST be removed from working tree and history
The team SHALL remove the leaked value from the working tree (replaced with a
placeholder) and purge it from all local git history, since the repository is
public. Rotation in Stripe (Requirement 1) is the actual remediation; the
history purge is best-effort hygiene.

#### Scenario: Remove from working tree
- **WHEN** the docs file references the leaked secret
- **THEN** the literal value is replaced with the placeholder `whsec_xxxx`

#### Scenario: Purge from local history
- **WHEN** the value exists in past commits
- **THEN** it is stripped from all local commits/blobs via a history-rewrite
      tool (e.g. `git filter-repo`)
- **AND** a `git grep` across all local refs confirms the value is gone before push

#### Scenario: History rewrite does not reach GitHub's copy
- **WHEN** the local history is rewritten and force-pushed
- **THEN** the team still treats the secret as permanently compromised
- **AND** requests GitHub Support to purge retained commit objects and audits
      forks/PRs, because the rewrite alone does not clear those copies

### Requirement: GitHub alert MUST be closed after remediation
The team SHALL ensure the secret-scanning alert is resolved (closed as "revoked"
or removed) only after the secret is rotated, removed from the tree, and purged
from history.

#### Scenario: Close alert
- **WHEN** rotation, tree removal, and history purge are complete
- **THEN** the `stripe_webhook_signing_secret` alert is closed as "revoked"

#### Scenario: Alert removed with the repository
- **WHEN** the GitHub repository containing the alert is deleted and recreated
      from clean history
- **THEN** the original alert no longer exists; the recreated repo has no
      secret-scanning alert because its history is clean (satisfies closure)
