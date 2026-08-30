## Context

The `open_portal` action in `artworks/admin.py` creates a Stripe billing portal session, then shows the URL as a plain-text success message before redirecting back to the change form. The button label says "Abrir" (Open), but the action doesn't open anything — it gives the admin a URL to copy-paste manually.

The Stripe billing portal session is created with a `return_url` (`settings.STRIPE_PORTAL_RETURN_URL`) that lets the user return to a neutral landing page after managing their subscription.

## Goals / Non-Goals

**Goals:**
- Make "Abrir Customer Portal" actually open the Stripe portal in the browser
- Keep the change minimal (one method, one test, one spec)

**Non-Goals:**
- Changing copy/regenerate/sync actions
- Modifying the copy button behavior
- Adding new model fields or state

## Decisions

### Redirect to the portal URL instead of showing a message

**Current**: `messages.success(request, gettext("Customer Portal: {url}").format(url=session.url))` then `return redirect(redirect_url)`

**Proposed**: `return redirect(session.url)`

**Rationale**: A redirect is the most natural behavior for a button labeled "Abrir". It opens the portal in one click. The portal URL is ephemeral (~30 min), so showing it in a message adds no value. Django's `redirect()` accepts external URLs and returns an `HttpResponseRedirect`.

**Alternatives considered:**
- `mark_safe()` in message to render clickable `<a target="_blank">`: adds HTML-in-messages footgun pattern, still requires two clicks
- Dynamic copy button for portal URL: requires storing ephemeral portal URL or creating a session on every page load — overkill for a 30-min URL

### Open in a new browser tab via Unfold `attrs`

The Unfold `@action` decorator accepts an `attrs` dict that is rendered directly as HTML attributes on the action's `<a>` element. Setting `attrs={"target": "_blank"}` opens the action URL (and thus the portal redirect) in a new tab, keeping the admin in the current tab.

The `return_url` already wired in `create_billing_portal_session` (`settings.STRIPE_PORTAL_RETURN_URL`) means the Stripe portal shows a "Return to app" link, so the admin can return to a neutral page after managing the subscription.

**Alternatives considered:**
- JS-level `window.open` on the button: more complex, requires template override or custom JS. Unfold's `attrs` achieves the same result with zero overhead.

## Risks / Trade-offs

- **Admin stays in Django, new tab for portal** → Each click creates a fresh ephemeral portal session in a new tab. The admin tab remains on the change form. No navigation disruption.
- **No way to copy the URL from admin** → The portal URL is ephemeral (~30 min) and created on-demand. Copying it has no use case since the button already opens it.
