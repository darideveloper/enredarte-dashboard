## Why

Production SMTP delivery failed with the STARTTLS-only defaults (`EMAIL_USE_TLS=True`, no `EMAIL_USE_SSL` knob): the working tree already carries the fix (`EMAIL_USE_TLS` default `False`, new `EMAIL_USE_SSL` default `True` in `project/settings.py:42-43`), but it is uncommitted, unspecified, and desynced from docs/examples. This change ratifies that manual edit so prod mail (cash subscription notifications) actually sends.

## What Changes

- Ratify `project/settings.py`: `EMAIL_USE_TLS` defaults to `False`, new `EMAIL_USE_SSL` defaults to `True` (both still env-overridable, explicit env always wins).
- Document the TLS (STARTTLS, port 587) vs SSL (implicit TLS, port 465) matrix and their mutual exclusivity in `docs/django-project-setup.md` email block.
- Document `EMAIL_USE_SSL` in `.env.dev.example` and `.env.prod.example` with the correct port pairing per environment.
- No change to the mailer service (`subscriptions/services/notifications.py`), templates, best-effort failure semantics, or cash-transition behavior.

## Capabilities

### New Capabilities

- None (no new user-facing capability; this is settings plumbing).

### Modified Capabilities

- `email-notifications`: settings requirement gains `EMAIL_USE_SSL`, new TLS/SSL defaults, and the mutual-exclusivity + port-pairing rule.

## Impact

- Affected code: `project/settings.py:36-45` (email block only).
- Docs/examples: `docs/django-project-setup.md:385-398`, `.env.dev.example`, `.env.prod.example`.
- Systems: production SMTP delivery for cash emails; dev (console backend) and tests (locmem) unaffected — both ignore TLS/SSL flags.
- Risk: operators who set `EMAIL_USE_TLS=True` without touching `EMAIL_USE_SSL` would get both `True` (Django `ValueError`); the design mitigates via documented defaults and port pairing, not new runtime validation.
