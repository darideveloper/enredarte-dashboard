"""Central brand tokens for transactional email (Gallery Salon system).

Single source of truth for the visual language of all transactional mail
(artwork sales + subscriptions), mirroring the landing's design tokens
(``DESIGN.md`` / ``src/styles/global.css`` in enredarte-landing). Templates
must reference these tokens via the ``brand`` context variable injected by
``core.mail_utils.send_audience`` (and ``subscriptions`` sender contexts) —
never hardcode brand hex values in per-mail templates.
"""

from django.utils import timezone

BRAND = {
    "paper": "#F2EDE4",
    "card": "#FFFFFF",
    "ink": "#1A1A1A",
    "crimson": "#C41E3A",
    "muted": "#8A8478",
    "border": "#E0DDD8",
    "banner_bg": "#EAE4D8",
    "description": "#7A7568",
}

WORDMARK = "ENREDARTE"

FOOTER_CONTACT = "info@enredarte.com"


def brand_context(extra=None):
    """Return brand/footer context merged over ``extra`` (caller wins)."""
    ctx = {
        "brand": BRAND,
        "wordmark": WORDMARK,
        "footer_contact": FOOTER_CONTACT,
        "year": timezone.now().year,
    }
    if extra:
        ctx.update(extra)
    return ctx
