"""Stripe SDK compatibility helpers.

Stripe Python >=15 blocks dict methods (e.g. .get) on StripeObject
(stripe/_stripe_object.py:163 raises AttributeError "is a dict method").
Use these helpers for version-agnostic access to plain dicts and
StripeObjects (Subscription, Price, etc.).
"""


def sget(obj, key, default=None):
    """Version-agnostic ``get`` for plain dict and StripeObject.

    StripeObject is a ``dict`` subclass but in stripe>=15 ``obj.get`` raises.
    This tries ``__getitem__`` first (works for both), then falls back to
    attribute access.
    """
    if obj is None:
        return default
    try:
        return obj[key]
    except KeyError:
        return default
    except TypeError:
        return getattr(obj, key, default)
    except AttributeError:
        return getattr(obj, key, default)


def to_plain_dict(obj):
    """Convert StripeObject or dict to plain dict for JSONField storage."""
    if obj is None:
        return {}
    if hasattr(obj, "to_dict"):
        try:
            return obj.to_dict()
        except Exception:
            pass
    if isinstance(obj, dict):
        return dict(obj)
    return obj
