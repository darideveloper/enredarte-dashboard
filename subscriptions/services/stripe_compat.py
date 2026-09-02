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


def _convert_decimals(value):
    """Recursively convert Decimal to string for JSON serialization."""
    from decimal import Decimal

    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, dict):
        return {k: _convert_decimals(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_convert_decimals(v) for v in value]
    return value


def to_plain_dict(obj):
    """Convert StripeObject or dict to plain JSON-serializable dict.

    Uses ``to_dict(for_json=True)`` when available (stripe>=15) to handle
    Decimals, otherwise falls back to plain ``to_dict`` / ``dict`` and
    recursively converts remaining Decimals to strings.
    """
    if obj is None:
        return {}
    data = None
    if hasattr(obj, "to_dict"):
        try:
            # stripe>=15 supports for_json=True for Decimal handling
            try:
                data = obj.to_dict(for_json=True)
            except TypeError:
                data = obj.to_dict()
        except Exception:
            pass
    if data is None:
        if isinstance(obj, dict):
            data = dict(obj)
        else:
            data = obj
    # Ensure nested Decimals (e.g. unit_amount_decimal) are JSON-serializable
    return _convert_decimals(data)
