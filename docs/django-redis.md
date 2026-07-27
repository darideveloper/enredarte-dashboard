---
created: 2026-05-30
updated: 2026-05-30
tags:
  - django
  - redis
  - celery
  - cache
type: resource
status: active
---

# Redis in Django Integration Guide

This guide details how to implement [[30-resources/redis/redis.md|Redis]] in a Django project for caching and background tasks.

## 📦 Dependencies

Add these to your `requirements.txt` (see [[20-areas/work/django/django-project-setup.md]]):

```text
django-redis>=5.4.0
celery[redis]>=5.4.0
```

## ⚙️ Configuration (`settings.py`)

### 1. Cache Backend
Using `django-redis` allows for persistent connections and advanced features.

```python
# settings.py
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": os.getenv("REDIS_URL", "redis://127.0.0.1:6379") + "/0",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}
```

### 2. Celery Broker
Configure Redis as the message broker for background workers.

```python
# settings.py
CELERY_BROKER_URL = os.getenv("REDIS_URL", "redis://127.0.0.1:6379") + "/1"
CELERY_RESULT_BACKEND = os.getenv("REDIS_URL", "redis://127.0.0.1:6379") + "/1"
```

> **Pro Tip:** Use database index `/0` for caching and `/1` for Celery to avoid collisions during cache clears.

## 🚀 Use Cases

### A. View Caching
Cache entire views to avoid hitting [[30-resources/postgresql/postgresql.md|PostgreSQL]].

```python
from django.views.decorators.cache import cache_page

@cache_page(60 * 15) # Cache for 15 minutes
def my_expensive_view(request):
    ...
```

### B. Background Tasks
Offload heavy tasks as described in [[20-areas/work/django/django-local-subdomain-setup.md]].

```python
from celery import shared_task

@shared_task
def process_media_upload(file_id):
    # Logic for processing files (see [[20-areas/work/django/django-media-storage.md]])
    ...
```

### C. Manual Caching
```python
from django.core.cache import cache

def get_data():
    data = cache.get('my_key')
    if not data:
        data = ExpensiveModel.objects.all()
        cache.set('my_key', data, 3600)
    return data
```

## 🔑 Environment Variables

| Variable | Description | Default |
| :--- | :--- | :--- |
| `REDIS_URL` | Base URL for Redis | `redis://127.0.0.1:6379` |

---
**Related:**
- [[30-resources/redis/redis.md|General Redis Resource]]
- [[20-areas/work/django/django-project-setup.md|Django Project Setup]]
- [[30-resources/docs/coolify-services.md|Coolify Services]]
