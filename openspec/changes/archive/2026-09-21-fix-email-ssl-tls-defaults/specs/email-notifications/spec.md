## MODIFIED Requirements

### Requirement: Email settings and environments
The system SHALL define `EMAIL_BACKEND`, `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS`, `EMAIL_USE_SSL`, `EMAIL_FROM`, and `EMAILS_NOTIFICATIONS` (comma-separated admin recipient list) in `project/settings.py`, following the block documented in `docs/django-project-setup.md:388`. `EMAIL_USE_TLS` SHALL default to `False` and `EMAIL_USE_SSL` SHALL default to `True` (each overridable via environment; explicit env always wins). `EMAIL_USE_TLS` and `EMAIL_USE_SSL` SHALL NOT both be `True` (Django forbids it); for real SMTP the valid pairs are STARTTLS with port `587` (`EMAIL_USE_TLS=True`, `EMAIL_USE_SSL=False`) or implicit SSL with port `465` (`EMAIL_USE_TLS=False`, `EMAIL_USE_SSL=True`). The no-env defaults (`EMAIL_USE_TLS=False`, `EMAIL_USE_SSL=True`, `EMAIL_PORT=587`) are console-ignored in dev/test; production SHALL set explicitly paired host/port/flag values from the environment. Dev/test environments SHALL default to the console backend (no credentials needed); production SHALL use SMTP with credentials from the environment. `.env.dev.example` and `.env.prod.example` SHALL document all new variables including `EMAIL_USE_SSL` with the correct port pairing.

#### Scenario: Dev sends to console without credentials
- **WHEN** a cash email fires in the dev environment with no SMTP variables set
- **THEN** the email content SHALL be printed to the runserver console and no network call SHALL occur.

#### Scenario: Tests capture mail in outbox
- **WHEN** any test triggers a cash transition
- **THEN** the emails SHALL be captured via Django's `locmem` backend and assertable through `django.core.mail.outbox` with no extra test dependency.

#### Scenario: Defaults select implicit SSL without env
- **WHEN** settings are imported with no `EMAIL_USE_TLS` / `EMAIL_USE_SSL` / `EMAIL_PORT` overrides
- **THEN** `EMAIL_USE_TLS` SHALL be `False` and `EMAIL_USE_SSL` SHALL be `True`.
