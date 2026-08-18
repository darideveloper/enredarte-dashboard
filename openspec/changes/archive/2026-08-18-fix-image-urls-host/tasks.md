## 1. Fix env loading in settings.py

- [x] 1.1 Change `load_dotenv(BASE_DIR / f".env.{ENV}")` to `load_dotenv(BASE_DIR / f".env.{ENV}", override=True)` in `project/settings.py`

## 2. Harden get_media_url in utils/media.py

- [x] 2.1 Add guard: if `settings.HOST` is `None` or empty, return the relative URL as-is
- [x] 2.2 Add guard: if `settings.HOST` is set but lacks `://`, log a warning and return the relative URL

## 3. Update documentation

- [x] 3.1 Update `docs/django-project-setup.md` dotenv loading snippet (lines 192-197) to show `override=True`
- [x] 3.2 Update `docs/django-project-setup.md` `get_media_url` code example (lines 556-572) to include the new guards

## 4. Verify

- [x] 4.1 Run existing tests to confirm no regressions
- [x] 4.2 Manually verify API image URLs return correct HOST prefix
