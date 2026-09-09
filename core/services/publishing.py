import logging
import urllib.error
import urllib.request

from django.conf import settings

logger = logging.getLogger(__name__)

WEBHOOK_TIMEOUT = 10


def publish_changes() -> bool:
    """Trigger the Coolify redeploy webhook, or succeed locally when unconfigured.

    Returns True on success. Raises RuntimeError on webhook failure so the
    caller can surface an error message. Never logs the webhook URL or token.
    """
    url = settings.DEPLOY_WEBHOOK_URL
    if not url:
        logger.info("publish_changes: webhook unconfigured, local success")
        return True
    token = settings.COOLIFY_API_TOKEN
    if not token:
        raise RuntimeError("COOLIFY_API_TOKEN sin configurar")
    # ponytail: GET + query params is Coolify's canonical webhook call (matches
    # the proven n8n pattern). Custom UA because Cloudflare (error 1010)
    # blocks Python-urllib/* at the edge before the request reaches Coolify.
    request = urllib.request.Request(url)
    request.add_header("Authorization", f"Bearer {token}")
    request.add_header("User-Agent", "enredarte-dashboard/1.0")
    try:
        with urllib.request.urlopen(request, timeout=WEBHOOK_TIMEOUT) as response:
            status = response.status
    except urllib.error.HTTPError as exc:
        logger.error("publish_changes: deploy webhook failed status=%s", exc.code)
        try:
            body = exc.read().decode("utf-8", "replace")
        except Exception:
            body = ""
        if "1010" in body or "cloudflare" in body.lower():
            raise RuntimeError(
                "Cloudflare bloqueó la petición (error 1010): revise las "
                "reglas WAF/Bots para /api/v1/*"
            ) from exc
        if exc.code in (401, 403):
            raise RuntimeError(
                "Coolify rechazó la petición (401/403): verifique "
                "COOLIFY_API_TOKEN y su permiso deploy"
            ) from exc
        raise RuntimeError(f"webhook devolvió {exc.code}") from exc
    except Exception as exc:
        logger.error("publish_changes: deploy webhook failed")
        raise RuntimeError(str(exc)) from exc
    if 200 <= status < 300:
        logger.info("publish_changes: deploy webhook ok status=%s", status)
        return True
    logger.error("publish_changes: deploy webhook bad status status=%s", status)
    raise RuntimeError(f"webhook devolvió {status}")
