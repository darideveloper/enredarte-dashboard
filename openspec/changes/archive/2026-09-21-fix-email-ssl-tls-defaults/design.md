## Context

`project/settings.py:36-45` holds the only email plumbing in the project, introduced by `2026-09-19-cash-payments-email-notifications` with a STARTTLS-only shape (`EMAIL_USE_TLS` default `True`, no `EMAIL_USE_SSL`). The working tree already flips this to `EMAIL_USE_TLS` default `False` + new `EMAIL_USE_SSL` default `True`, but `openspec/specs/email-notifications/spec.md:7`, `docs/django-project-setup.md:389-397`, `.env.dev.example`, and `.env.prod.example` still describe the old shape. Dev (console backend) and tests (locmem) ignore both flags, so the breakage is prod-only and silent (best-effort sender logs + warns, keeps state per `email-notifications` spec).

## Goals / Non-Goals

**Goals:**

- Ratify the two-line settings fix as the canonical default (SSL-first, TLS opt-in via env).
- Pin the TLS-vs-SSL mutual exclusivity and port pairing (`587↔TLS`, `465↔SSL`) in spec + docs + examples so operators can't land in a both-`True` or wrong-port state by following defaults.
- Keep the change to plumbing + docs: no mailer, template, or cash-flow edits.

**Non-Goals:**

- No runtime validation (no `check` error, no startup guard) — env-explicit misconfiguration remains operator responsibility.
- No per-environment auto-switching (no "if port is 465 then SSL") — explicit flags only.
- No change to failure semantics (best-effort send stays).

## Decisions

- **SSL-first defaults (`TLS=False`, `SSL=True`), env-overridable.** Rationale: matches the already-present manual fix (uncommitted working-tree edit) and the prod provider that needs implicit SSL; anyone on STARTTLS sets two explicit vars (`EMAIL_USE_TLS=True`, `EMAIL_USE_SSL=False`) with the documented port. Alternative (revert to TLS-only) rejected: it re-breaks the prod delivery this change exists to fix. Alternative (both default `False`) rejected: plain SMTP by default is worse than either secure mode.
- **Docs + examples carry the port matrix, not code.** Rationale: minimal/YAGNI — three comment lines across settings/docs/examples prevent the both-`True` and `SSL+587` traps with zero new code paths to test. Alternative (auto-derive SSL from port) rejected: magic coupling between two independent env vars.
- **Spec delta is MODIFIED, not ADDED.** Rationale: the existing "Email settings and environments" requirement already owns this block; the change edits its SHALL list and adds one scenario rather than inventing a new capability.

## Risks / Trade-offs

- [Both-`True` operator config → Django `ValueError` at send, surfaced as mail warning + kept state] → Mitigation: spec + docs state mutual exclusivity; examples show exactly one mode per environment.
- [`SSL=True` + `PORT=587` inheritance from stale `.env` files] → Mitigation: examples updated to paired values; docs comment shows the two valid pairs.
- [Dev/console masks prod misconfig] → Mitigation: new spec scenario asserts defaults by settings import (no SMTP needed); real handshake verified manually once per provider, not in CI.
