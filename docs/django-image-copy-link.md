---
created: 2026-04-18
updated: 2026-04-18
tags:
  - django
  - admin
  - documentation
type: resource
status: active
---

# Image Copy Link Feature

This document describes how the "Copy Link" feature for the `Image` model in the `blog` app is implemented.

## Overview

The feature allows administrators to copy the public URL of an uploaded image to their clipboard with a single click from the Django Admin interface.

## Backend Implementation

The backend logic is handled within the `ImageAdmin` class in `blog/admin.py`.

### Admin Action: `copy_link`

The `copy_link` method is decorated with `@action` from `unfold.decorators`, making it available as a row action in the Unfold admin theme.

```python
@action(description="Copy link")
def copy_link(self, request: HttpRequest, object_id: int):
    obj = self.get_object(request, object_id)

    # Get url and show message
    image_url = get_media_url(obj.image.url)
    messages.success(request, f"Copied to clipboard: {image_url}")

    # Redirect to the same page with a cookie
    response = redirect(request.META.get("HTTP_REFERER", ".."))
    response.set_cookie("copy_to_clipboard", image_url, max_age=10)

    return response
```

**Key Steps:**
1.  **Retrieve Object:** Fetches the `Image` object using `object_id`.
2.  **Generate URL:** Uses `get_media_url` to get the absolute URL (handling both local storage and cloud providers).
3.  **Success Message:** Adds a Django success message to be displayed on the next page load.
4.  **Cookie Strategy:** Instead of copying directly (which isn't possible from the server-side), it sets a short-lived cookie `copy_to_clipboard` containing the image URL.
5.  **Redirect:** Redirects the user back to the list view or change page.

### Utility: `get_media_url`

Located in `utils/media.py`, this utility ensures the URL is absolute and prefixed with the correct host if necessary.

```python
def get_media_url(object_or_url: object) -> str:
    # ... logic to prepend settings.HOST for local files
    # ... or return absolute URLs for S3/DO Spaces
```

## Frontend Implementation

The frontend logic is handled by `static/js/copy_clipboard.js`, which is included in the `ImageAdmin` via the `Media` class.

### JavaScript Handler: `copy_clipboard.js`

This script listens for the `DOMContentLoaded` event and checks for the presence of the `copy_to_clipboard` cookie.

```javascript
document.addEventListener('DOMContentLoaded', () => {
  const getCookie = (name) => {
    // ... logic to extract cookie value
  }

  const url = getCookie('copy_to_clipboard')
  if (url) {
    navigator.clipboard.writeText(url).then(() => {
      // Clear the cookie immediately after copying
      document.cookie = "copy_to_clipboard=; path=/; Max-Age=-99999999;"
    })
  }
})
```

**Workflow:**
1.  **Check Cookie:** On page load, it searches for `copy_to_clipboard`.
2.  **Clipboard API:** If the cookie exists, it uses `navigator.clipboard.writeText(url)` to copy the content.
3.  **Cleanup:** Once the copy is successful, it clears the cookie to prevent repeated copies on subsequent refreshes.

## Summary of Files Involved

- `blog/admin.py`: Defines the admin action and includes the JS.
- `utils/media.py`: Provides the URL generation logic.
- `static/js/copy_clipboard.js`: Handles the actual clipboard interaction on the client-side.
- `project/settings.py`: Provides the `HOST` setting used for absolute URL generation.
