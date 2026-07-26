## ADDED Requirements

### Requirement: Multi-stage Dockerfile
The system SHALL create a `Dockerfile` using `python:3.12-slim` base image with `PYTHONDONTWRITEBYTECODE=1` and `PYTHONUNBUFFERED=1`. It SHALL set `WORKDIR /app`, copy project files, make `start.sh` executable, and accept all configuration as `ARG`/`ENV` pairs (grouped: Django DB, AWS/Storage, General). It SHALL install system dependencies (`libpq-dev gcc`), install Python packages from `requirements.txt`, run `collectstatic --noinput` during build, expose port 80, and `CMD ["./start.sh"]`.

#### Scenario: Docker build succeeds
- **WHEN** `docker build .` is executed
- **THEN** all Python packages SHALL install and `collectstatic` SHALL complete without errors

#### Scenario: Build args passed to env
- **WHEN** build args like `SECRET_KEY`, `DB_ENGINE`, `STORAGE_AWS` are provided
- **THEN** they SHALL be available as `ENV` during the `RUN pip install` and `RUN collectstatic` steps

### Requirement: start.sh deployment script
The system SHALL create `start.sh` with `#!/bin/sh`, `set -e`, running `python manage.py makemigrations --noinput`, `python manage.py migrate --noinput`, then `exec gunicorn --bind 0.0.0.0:80 project.wsgi:application`.

#### Scenario: Container starts correctly
- **WHEN** the container launches
- **THEN** migrations SHALL run automatically and Gunicorn SHALL bind to 0.0.0.0:80

### Requirement: dev.sh local development script
The system SHALL create `dev.sh` that checks for an existing tmux session named `${PROJECT_NAME}_dev`, starts `portless proxy start` and `portless trust`, dynamically finds a free port starting from 8000 using `ss -tuln`, detects the virtual environment (`venv/` or `.venv/`), creates a tmux session with one window running `portless enredarte --app-port $PORT -- python manage.py runserver $PORT`, and attaches to the session.

#### Scenario: First run creates session
- **WHEN** `./dev.sh` is executed with no existing tmux session
- **THEN** portless SHALL start, a free port SHALL be found, Django SHALL run, and the app SHALL be accessible at `https://enredarte.localhost`

#### Scenario: Re-attach to existing session
- **WHEN** `./dev.sh` is executed and a `${PROJECT_NAME}_dev` tmux session already exists
- **THEN** the script SHALL attach to the existing session without creating a new one

### Requirement: Port conflict resolution
dev.sh SHALL loop through ports starting at 8000, incrementing until `ss -tuln | grep -q ":$PORT "` returns false, ensuring no port collision with other running Django projects.

#### Scenario: Port 8000 already in use
- **WHEN** another project is using port 8000
- **THEN** dev.sh SHALL use port 8001 (or the next available port)

### Requirement: Environment variables for subdomain access
For local development with portless, `.env.dev` SHALL include `ALLOWED_HOSTS=localhost,127.0.0.1,enredarte.localhost`, `CORS_ALLOWED_ORIGINS=https://enredarte.localhost`, `CSRF_TRUSTED_ORIGINS=https://enredarte.localhost`, and `HOST=http://localhost:8000`. For production, `.env.prod` SHALL include `HOST=` as a placeholder.

#### Scenario: Subdomain access works
- **WHEN** the browser navigates to `https://enredarte.localhost`
- **THEN** Django SHALL accept the request (no 400 Bad Request) and CORS headers SHALL allow the origin

### Requirement: requirements.txt with all dependencies
The system SHALL create `requirements.txt` with pinned versions for all required packages: Django>=5.2,<5.3, whitenoise>=6.11.0, gunicorn>=24.1.1, django-cors-headers>=4.9.0, python-dotenv>=1.0.1, psycopg>=3.2.3, pillow>=11.1.0, djangorestframework>=3.16.1, django-filter>=24.3, selenium>=4.40.0, django-unfold==0.77.1, django-solo>=2.3.0, requests>=2.32.3, django-storages==1.14.4, boto3==1.34.162.

#### Scenario: All packages installable
- **WHEN** `pip install -r requirements.txt` is run
- **THEN** all packages SHALL install successfully with compatible versions

### Requirement: Virtual environment handling
dev.sh SHALL detect if `venv/` or `.venv/` exists and prefix commands with the appropriate activation (`source venv/bin/activate &&` or `source .venv/bin/activate &&`).

#### Scenario: venv detected and activated
- **WHEN** `venv/` exists in the project root
- **THEN** the Django runserver command SHALL be prefixed with `source venv/bin/activate &&`

### Requirement: Chrome testing placeholder
The `requirements.txt` SHALL include `selenium>=4.40.0` and the `utils/automation.py` utility SHALL be created with a `get_selenium_elems` helper function for future E2E testing, even though no tests exist yet.

#### Scenario: Selenium importable
- **WHEN** `from utils.automation import get_selenium_elems` is executed
- **THEN** the function SHALL be importable without errors
