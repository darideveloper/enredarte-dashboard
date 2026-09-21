## 1. Settings ratification

- [x] 1.1 Verify `project/settings.py:43-44` keeps `EMAIL_USE_TLS` default `False` and `EMAIL_USE_SSL` default `True` (already in working tree; no-op if unchanged).
- [x] 1.2 Add a one-line comment above the flags stating TLS/SSL are mutually exclusive with the valid pairs (`587`+TLS vs `465`+SSL).

## 2. Docs and examples sync

- [x] 2.1 Update `docs/django-project-setup.md:385-398` email block to match settings (both flags, defaults, pairing note).
- [x] 2.2 Document `EMAIL_USE_SSL` with the correct port pairing in `.env.dev.example` (commented SMTP example) and `.env.prod.example` (live values).

## 3. Verification

- [x] 3.1 Run `venv/bin/python manage.py check` (settings import clean).
- [x] 3.2 Run `venv/bin/python manage.py test subscriptions --verbosity=2` (mail paths still pass via locmem; no new test dep).
- [x] 3.3 Assert defaults by settings import (no `EMAIL_USE_TLS`/`EMAIL_USE_SSL` overrides → `False`/`True`).
