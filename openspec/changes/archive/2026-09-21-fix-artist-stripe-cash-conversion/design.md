## Context

All affected logic lives in `artworks/admin.py` `ArtistAdmin`. The cash flow is governed by `_is_online_started()` (`artworks/admin.py:479`) — the single predicate used both to hide the "Marcar como efectivo" button (`has_marcar_efectivo_permission`, `:487`) and to refuse its direct URL (`marcar_efectivo`, `:729`). It returns "online has started" for *any* online row with a `signup_url`, `stripe_customer_id`, or `stripe_subscription_id` — so a single generated, never-paid link locks the artist out of cash permanently.

The four Stripe actions (`generate_link`, `regenerate_link`, `open_portal`, `sync_from_stripe`) all call into `subscriptions/services/stripe_client.py` with the stored `stripe_customer_id`. None recovers from a deleted/broken customer: the generic `except stripe.error.StripeError` (prefix `Stripe no respondió`) fails the action and leaves the stale id in place forever.

Stripe SDK is pinned to `>=15.5.1,<16`. Stripe's checkouts endpoint reports a nonexistent/deleted customer as an `InvalidRequestError`. Tests mock the client via `unittest.mock.patch`, so the real error shape is exercised only by integration; the predicate must be defensive.

## Goals / Non-Goals

**Goals:**
- Allow "Marcar como efectivo" for online rows that are not actively billing (never-paid `pending`, `canceled`, `canceling`, and `active` with `cancel_at_period_end`).
- Keep it blocked while a live subscription is actually billing (`active` not cancel-requested, `past_due`).
- Ensure cash rows carry no stale `stripe_customer_id`/`stripe_subscription_id`.
- Make all four Stripe actions recover (not hard-fail) from a deleted/broken Stripe customer.
- Keep operator messages Spanish, matching the existing admin style.

**Non-Goals:**
- No model/migration or dependency changes.
- No changes to artwork checkout flow (it uses `customer_email`, not a stored customer id — not affected).
- No Stripe-side cleanup of orphaned/deleted customers.

## Decisions

### Decision 1 — Cash conversion blocking predicate is status-driven

Replace `_is_online_started` with a predicate that blocks conversion **only** when a live subscription is billing:

```
blocks = sub.payment_method == ONLINE
         AND ( status == PAST_DUE
               OR ( status == ACTIVE AND NOT cancel_at_period_end ) )
```

Allowed → `pending`, `canceled`, `canceling`, and `active`-with-cancel-requested. Because the same predicate feeds both the button and the URL guard, one change covers both layers — no per-caller patches.

| Alternative | Why rejected |
|---|---|
| Keep the old "any link/customer exists" guard | That is Bug 1; it incorrectly locks never-paid artists into online. |
| Also block whenever `stripe_subscription_id` is set | User explicitly chose status-only; a `pending` row with a stray id is a desync we tolerate in exchange for simpler behavior. |

### Decision 2 — Clear Stripe pointers when converting to cash

`marcar_efectivo` already clears `signup_url`/dates; extend the cleared set to `stripe_customer_id` and `stripe_subscription_id` so a previously-online (never-billing) row becomes a clean cash row. This does double duty: it honors the "Cash rows carry no Stripe identifiers" capability and removes any stale id that could resurface Bug 2 on a later return to online.

| Alternative | Why rejected |
|---|---|
| Keep the customer id on cash rows | User chose to clear; avoids serving a possibly-stale pointer and produces a clean cash row. |

### Decision 3 — Stale-customer detection predicate + retry-once in generate/regenerate

Add one predicate `_is_stale_customer_error(e, customer_id)`: `True` when the error is a Stripe request error referencing the stored customer as missing/deleted. Grounded on Stripe 15.5.1 behavior: `InvalidRequestError` with `code == "resource_missing"` and/or the customer id appearing in the error text/`param`.

In `generate_link`/`regenerate_link`, wrap the `create_checkout_session` call: on a stale-customer error, clear `stripe_customer_id`, create a fresh customer, and retry the session **once**. Only a second failure falls through to the existing "Stripe no respondió" path, preserving all current log/`messages.error`/302 semantics for genuine outages.

| Alternative | Why rejected |
|---|---|
| Validate the customer with `retrieve` before every generation | Extra Stripe call on the happy path; reactive retry is cheaper and only acts when actually needed. |
| Recreate on *any* `StripeError` | Would mask real transient/rate-limit failures behind a customer recreate + retry; too broad. The predicate is narrow on purpose. |

### Decision 4 — open_portal / sync_from_stripe: clear + targeted warning

These two cannot proceed with a recreated customer (a portal session needs a real subscription; sync lists subs under the customer). On a stale-customer error they clear `stripe_customer_id` and show a targeted Spanish warning — `"El customer fue eliminado de Stripe; regenera el link"` — instead of the generic `Stripe no respondió`. Clearing means the next `generate_link` creates a fresh customer, breaking the dead-id loop.

| Alternative | Why rejected |
|---|---|
| Recreate a customer for portal/sync | Pointless — no subscription exists under a freshly created customer; would also mutate state we don't own. |

## Risks / Trade-offs

- **Status-only blocking can race with a live payment.** A row whose Stripe subscription just got created but the webhook hasn't landed (status still `pending`) could be converted to cash. → Mitigation: `marcar_efectivo` clears `stripe_subscription_id`/`stripe_customer_id`; a late webhook on a cash row is already ignored by webhook handlers (cash rows skip Stripe tracking). Accepted as an edge case.
- **Stale-customer predicate depends on Stripe error shape.** If Stripe changes how it reports a deleted customer, the predicate could miss. → Mitigation: predicate also matches the customer id appearing in the message text, not only `code`; integration-test once. If it misses, the action falls back to the existing generic `Stripe no respondió` path (no worse than today).
- **Retry-once creates a new Stripe customer.** If the original customer was not actually deleted but the error was transient, we may orphan a customer. → Mitigation: retry is bounded to once and only on the narrow stale-customer signal; the error message/`param` disambiguate. Minor Stripe-side orphan is acceptable and logged by the existing `logger.warning`.

## Migration Plan

No data migration required — existing rows are untouched. Deploy:
1. Merge code + tests.
2. Run `venv/bin/python manage.py test` (or the `subscriptions.tests...` labels).
3. No manual backfill; stale rows self-heal on the next operator action (cash conversion clears ids; generate/regenerate run recovery).

## Open Questions

- None blocking. The exact Stripe `code` for a *deleted* (vs. never-existing) customer will be confirmed during implementation by capturing a real error; the message-text fallback in the predicate covers both.