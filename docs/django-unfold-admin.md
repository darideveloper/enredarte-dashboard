---
created: 2026-04-18
updated: 2026-04-18
tags:
  - django
  - admin
  - unfold
  - documentation
type: resource
status: active
---

# Django Unfold Integration Guide

This document describes how `django-unfold` is integrated into this project to provide a modern, responsive, and customizable Django Admin interface.

## 0. Prerequisites

Before proceeding, ensure the core infrastructure (Environment Variables, Static Files, and Templates) has been set up following the [Project Setup Guide](project-setup.md).

## 1. Dependencies

Add the following package to your `requirements.txt`:

```text
django-unfold==0.77.1
```

## 2. Configuration in `settings.py`

### 2.1 Installed Apps

Ensure `unfold` and its optional components are placed **before** `django.contrib.admin`:

```python
INSTALLED_APPS = [
    "unfold",
    "unfold.contrib.filters",
    "unfold.contrib.forms",
    "unfold.contrib.inlines",
    "rest_framework.authtoken",
    # ... other apps
    "django.contrib.admin",
    "django.contrib.auth",
    # ...
]
```

### 2.2 Static Files & Templates

Ensure root static and templates directories are configured in `settings.py` to allow overriding admin assets, as described in the [Project Setup Guide](project-setup.md#6-core-settings--app-integration).

## 3. UNFOLD Settings Dictionary

Key logic:
- **SITE_ICON**: When used, the **SITE_HEADER** and **SITE_SUBHEADER** remain visible in the sidebar.
- **SITE_FAVICONS**: When used, it replaces the **SITE_ICON**, but the **SITE_HEADER** and **SITE_SUBHEADER** remain visible.
- **SITE_LOGO**: When used, it replaces the **SITE_FAVICONS**, **SITE_HEADER**, and **SITE_SUBHEADER** in the sidebar.
- **COLORS**: Defined using OKLCH for modern browser support and consistent shading.
- **SIDEBAR**: `show_all_applications: True` with an empty `navigation: []` switches the sidebar to **auto-render mode**: every registered `ModelAdmin` in `INSTALLED_APPS` is listed, filtered by the request user's per-model permissions. The sidebar body is rendered by a project-level template override at `project/templates/unfold/helpers/navigation.html` (Unfold's bundled template falls back to Django's classic `admin/app_list.html` when `navigation` is empty, which is not Unfold-styled; the override is required to get an Unfold-styled auto sidebar). See §3.1 below.

```python
from django.templatetags.static import static
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

UNFOLD = {
    "SITE_TITLE": "leochan.sh Dashboard",
    "SITE_HEADER": "leochan.sh Admin", # Fallback when logo is missing
    "SITE_SUBHEADER": "leochan.sh Dashboard", # Visible below logo
    "SITE_URL": "/",
    "SITE_ICON": lambda request: static("favicon.png"),
    "SITE_LOGO": lambda request: static("logo.webp"),
    "SITE_SYMBOL": "directions_car",
    "SITE_FAVICONS": [
        {
            "rel": "icon",
            "sizes": "32x32",
            "type": "image/png",
            "href": lambda request: static("favicon.png"),
        },
    ],
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": True,
    "ENVIRONMENT": "utils.callbacks.environment_callback",
    "THEME": "light",
    "COLORS": {
        "primary": {
            "50": "oklch(0.97 0.02 296)",
            "100": "oklch(0.92 0.04 296)",
            "200": "oklch(0.85 0.08 296)",
            "300": "oklch(0.75 0.15 296)",
            "400": "oklch(0.70 0.22 296)",
            "500": "oklch(0.68 0.28 296)",  # C92FFF
            "600": "oklch(0.60 0.25 296)",
            "700": "oklch(0.50 0.20 296)",
            "800": "oklch(0.40 0.16 296)",
            "900": "oklch(0.30 0.12 296)",
            "950": "oklch(0.20 0.08 296)",
        },
    },
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": False,
        "navigation": [
            {
                "title": _("Autenticación"),
                "separator": True,
                "collapsible": False, # Keep open by default
                "items": [
                    {
                        "title": _("Usuarios"),
                        "icon": "person",
                        "link": reverse_lazy("admin:auth_user_changelist"),
                    },
                ],
            },
            {
                "title": _("Tienda"),
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": _("Ventas"),
                        "icon": "payments",
                        "link": reverse_lazy("admin:store_sale_changelist"),
                    },
                ],
            },
            {
                "title": _("Sección de Traslados"),
                "separator": True,
                "items": [], # Used as a section divider
            },
            {
                "title": _("App Name"),
                "collapsible": True,
                "items": [
                    {
                        "title": _("Models"),
                        "icon": "directions_car",
                        "link": reverse_lazy("admin:app_model_changelist"),
                    },
                ],
            },
        ],
    },
}
```

> **Note**: the multi-group `navigation` example above is a reference snippet. In the `clients` project the sidebar is configured for **auto-render mode** (`navigation: []`, `show_all_applications: True`) so that adding a new `ModelAdmin` requires no settings change and the rendered list is filtered by the request user's per-model permissions. See §3.1.

### 3.1. Permission-aware auto sidebar

`UNFOLD["SIDEBAR"]` has no setting that auto-populates the sidebar body from registered `ModelAdmin` classes. The `show_all_applications` flag adds a single "All applications" **modal button** at the bottom of the sidebar — it does not render apps inline. An empty `navigation` causes Unfold's bundled `unfold/helpers/navigation.html` to fall back to Django's classic `admin/app_list.html` (boxed table markup, not Unfold styling).

To get an Unfold-styled, permission-filtered auto sidebar, this project overrides Unfold's helper at `project/templates/unfold/helpers/navigation.html`. The override iterates `available_apps` (Django's permission-filtered app list, provided by `AdminSite.get_app_list(request)`) using Unfold's group/link DOM, applies the `active` class set when a model's `admin_url` matches the request path, and falls back to the `unfold/helpers/messages/error.html` partial for users with no admin permissions.

Resulting `SIDEBAR` block in `project/settings.py`:

```python
"SIDEBAR": {
    "show_search": True,
    "show_all_applications": True,
    "navigation": [],
},
# No `permission` callback, no Python helper, no custom `AdminSite` subclass,
# and no `core/admin.py` changes are required.
```


## 4. Custom Callbacks (`utils/callbacks.py`)

Provides environment-specific badges in the admin header.

```python
import os

def environment_callback(request):
    env = os.getenv("ENV", "dev")
    env_mapping = {
        "prod": ["Production", "danger"],
        "staging": ["Staging", "warning"],
        "dev": ["Development", "info"],
        "local": ["Local", "success"],
    }
    return env_mapping.get(env, ["Unknown", "info"])
```

## 5. Static Assets (Unfold Enhancements)

These scripts enhance the Unfold interface with custom styling and functionality.

### static/css/style.css — `.img-preview`

Image preview thumbnails (e.g. `ArtworkAdmin.display_image`, `PostAdmin.display_banner`, `BlogImageAdmin.display_preview`) are styled by the `.img-preview` classes defined in `static/css/style.css` — **not** by inline `style=` attributes. Emit `class="img-preview"` and add a variant only when a non-default size or layout is needed:

```css
.img-preview { height: 50px; border-radius: 6px; object-fit: cover; }
.img-preview--sm { height: 40px; width: 40px; object-fit: cover; }
.img-preview--lg { height: 64px; width: 64px; object-fit: cover; }
```

Use `img-preview img-preview--sm` for small square thumbnails (e.g. changelist columns), plain `img-preview` for regular inlines, and `img-preview--lg` for larger square thumbnails. Previews must not use inline styles.

Form-field image previews (e.g. `Post.banner_image`, `BlogImage.image`) are handled by Unfold's native file-input widget and are **not** styled with `.img-preview` classes.

### static/js/load_markdown.js
Integrates SimpleMDE for all text areas within Unfold.
```javascript
document.addEventListener("DOMContentLoaded", () => {
  const textAreasSelector = "div > textarea"
  const textAreas = document.querySelectorAll(textAreasSelector)

  setTimeout(() => {
    textAreas.forEach((textArea) => {
      new SimpleMDE({
        element: textArea,
        toolbar: [
          "bold",
          "italic",
          "heading",
          "|",
          "quote",
          "code",
          "link",
          "image",
          "|",
          "unordered-list",
          "ordered-list",
          "|",
          "undo",
          "redo",
          "|",
          "preview",
        ],
        spellChecker: false,
      })
    })
  }, 100)
})
```

### static/js/range_date_filter_es.js
Localizes placeholder text for Unfold's range date filters.
```javascript
document.addEventListener("DOMContentLoaded", function () {
  const texts = [
    { names: ["created_at_from", "updated_at_from"], text: "Desde" },
    { names: ["created_at_to", "updated_at_to"], text: "Hasta" },
  ]

  texts.forEach((text) => {
    text.names.forEach((name) => {
      const elem = document.querySelector(`[name="${name}"]`)
      if (!elem) return
      elem.placeholder = text.text
    })
  })
})
```

### Markdown Preview Styling (`static/css/style.css`)
To ensure the Markdown preview is readable within the Unfold theme, custom typography styles are applied to `.editor-preview`. These styles re-introduce headings, lists, and other formatting that are otherwise stripped by Tailwind's reset, while using dynamic CSS variables for brand consistency.

```css
.editor-preview, .editor-preview-side {
    font-family: inherit;
    color: inherit;
    line-height: 1.6;
}

.editor-preview h1, .editor-preview-side h1 {
    font-size: 1.875rem;
    font-weight: 700;
    margin-top: 1.5rem;
    margin-bottom: 1rem;
    border-bottom: 1px solid var(--color-base-200);
    padding-bottom: 0.5rem;
}

.editor-preview h2, .editor-preview-side h2 {
    font-size: 1.5rem;
    font-weight: 700;
    margin-top: 1.25rem;
    margin-bottom: 0.75rem;
    border-bottom: 1px solid var(--color-base-100);
    padding-bottom: 0.25rem;
}

.editor-preview h3, .editor-preview-side h3 {
    font-size: 1.25rem;
    font-weight: 600;
    margin-top: 1rem;
    margin-bottom: 0.5rem;
}

.editor-preview p, .editor-preview-side p {
    margin-bottom: 1rem;
}

.editor-preview ul, .editor-preview-side ul {
    list-style-type: disc !important;
    padding-left: 1.5rem !important;
    margin-bottom: 1rem;
}

.editor-preview ol, .editor-preview-side ol {
    list-style-type: decimal !important;
    padding-left: 1.5rem !important;
    margin-bottom: 1rem;
}

.editor-preview li, .editor-preview-side li {
    display: list-item !important;
    margin-bottom: 0.25rem;
}

.editor-preview strong, .editor-preview-side strong {
    font-weight: 700;
}

.editor-preview em, .editor-preview-side em {
    font-style: italic;
}

.editor-preview blockquote, .editor-preview-side blockquote {
    border-left: 4px solid var(--color-base-200);
    padding-left: 1rem;
    color: var(--color-font-subtle-light);
    font-style: italic;
    margin-bottom: 1rem;
}

.editor-preview code, .editor-preview-side code {
    background-color: var(--color-base-100);
    padding: 0.2rem 0.4rem;
    border-radius: 0.25rem;
    font-family: monospace;
    font-size: 0.875em;
}

.editor-preview pre, .editor-preview-side pre {
    background-color: var(--color-base-100);
    padding: 1rem;
    border-radius: 0.5rem;
    overflow-x: auto;
    margin-bottom: 1rem;
}

.editor-preview pre code, .editor-preview-side pre code {
    background-color: transparent;
    padding: 0;
}

.editor-preview a, .editor-preview-side a {
    color: var(--brand-primary-600, var(--color-primary-600));
    text-decoration: underline;
}
```

### File Upload Widget Width (`static/css/style.css`)
Unfold's file/image upload widgets render a fake, disabled text input to show the filename or the "Seleccionar archivo para subir" placeholder. That input carries `grow` (`flex-grow: 1`) and `min-w-0` (`min-width: 0`) classes, but they are inert because its wrapping `<label class="grow relative">` is not a flex container, so the input stays at its intrinsic width and the label text is not fully visible. Making the label a flex container activates those classes and the input fills the widget width:

```css
label.grow.relative {
    display: flex;
}
```

The `label.grow.relative` selector matches only the two Unfold file-input widget templates (`clearable_file_input.html` and `clearable_file_input_small.html`), so it covers both the change-form widget and the small inline widget without touching other inputs. Do **not** use `width: 100%` on the input instead: it regresses the small inline widget (a circular flex/percentage sizing collapses the label and truncates the text).

### M2M FilterWidget Helptext Removal (`static/css/style.css`)

Django's `filter_horizontal`/`filter_vertical` widgets inject a `<p class="helptext">` into each side's title bar. The Spanish admin JS catalog translates the English hint ("…select the 'Choose' arrow button") as *"use el botón 'Elegir'"*, and the "Remove" side as *"use el botón 'Eliminar'"* — referencing labelled buttons that don't exist (the move controls are only arrows between the lists). The widget is self-explanatory (labelled lists + filters + arrows), so both hints are removed:

```css
.selector-available-title .helptext,
.selector-chosen-title .helptext {
    display: none;
}
```

`display:none` also drops the hints from the accessibility tree. The selectors match only the two hint paragraphs `SelectFilter2.js` injects; no other element in the admin uses `class="helptext"` inside `.selector-*-title`.

## 6. Admin Interface Overrides

Override the base admin template to inject SimpleMDE and other custom assets. To ensure Unfold's sticky bottom bar and responsive layout logic are preserved, always extend `"admin/base.html"` instead of the internal layout directly.

### project/templates/admin/base_site.html
```html
{% extends "admin/base.html" %} {% load static %} {% block extrahead %}
{{ block.super }}
<!-- Load markdown libraries -->
<link rel="stylesheet" href="https://cdn.jsdelivr.net/simplemde/latest/simplemde.min.css" />
<script src="https://cdn.jsdelivr.net/simplemde/latest/simplemde.min.js"></script>

<!-- Load Unfold custom scripts -->
<script src="{% static 'js/load_markdown.js' %}"></script>
<script src="{% static 'js/range_date_filter_es.js' %}"></script>
{% endblock %}
```

## 7. Admin Implementation

### 7.1 Customizing Auth Models (`project/admin.py`)

> **CRITICAL: `project/admin.py` is NOT auto-discovered** because `project` is not in `INSTALLED_APPS`. Django's admin autodiscovery only finds `admin.py` inside installed apps. You must explicitly import the module in `urls.py` for the custom admin classes to register:
> ```python
> # project/urls.py
> import project.admin  # ← required so UserAdmin, GroupAdmin, TokenAdmin are registered
> ```
> Without this import, Django's default admin classes are used silently — `sidebar_icon`, Unfold forms, and all other customisations are ignored.

All auth model admin classes SHALL use `ModelAdminUnfoldBase` (not raw `ModelAdmin`) to inherit `compressed_fields`, `warn_unsaved_form`, `sidebar_icon`, and the `edit` row action.

> **DRF-only**: `TokenAdmin` / `TokenProxy` (from `rest_framework.authtoken`) are only required if the project uses DRF's `TokenAuthentication`. If not using DRF or not using Token auth, omit those imports, the `unregister(TokenProxy)` call, and the `TokenAdmin` class.

```python
from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group, User
from rest_framework.authtoken.admin import TokenAdmin as BaseTokenAdmin
from rest_framework.authtoken.models import TokenProxy

from project.admin_base import ModelAdminUnfoldBase
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm

admin.site.unregister(User)
admin.site.unregister(Group)
admin.site.unregister(TokenProxy)


@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdminUnfoldBase):
    sidebar_icon = "person"
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm
    list_display = ("username", "email", "first_name", "is_staff")
    list_display_links = ("username", "email")


@admin.register(Group)
class GroupAdmin(BaseGroupAdmin, ModelAdminUnfoldBase):
    sidebar_icon = "group"


@admin.register(TokenProxy)
class TokenAdmin(BaseTokenAdmin):
    sidebar_icon = "key"
```
### 7.2 Base Admin Class (`ModelAdminUnfoldBase`)

Provides common UI enhancements like row actions and compressed fields.

```python
from unfold.admin import ModelAdmin
...
from unfold.decorators import action
from django.shortcuts import redirect
from django.urls import reverse

class ModelAdminUnfoldBase(ModelAdmin):
    sidebar_icon = "database"
    compressed_fields = True
    warn_unsaved_form = True
    list_filter_sheet = False
    change_form_show_cancel_button = True

    actions_row = ["edit"]

    @action(description="Edit", permissions=["change"])
    def edit(self, request, object_id):
        return redirect(reverse(f"admin:{self.model._meta.app_label}_{self.model._meta.model_name}_change", args=[object_id]))
```

**Custom sidebar icon per model.** The auto-rendered sidebar (`project/templates/unfold/helpers/navigation.html`) uses the `ModelAdminUnfoldBase.sidebar_icon` class attribute as the Material symbol for each model link. Default is `"database"`. Override per admin:

```python
@admin.register(Client)
class ClientAdmin(ModelAdminUnfoldBase):
    sidebar_icon = "directions_car"
```

The icon map is built by `utils.admin_icons.build_sidebar_icon_map()` and injected into every template via `utils.context_processors.user_palette`. The template reads the map through a `get_item` filter defined in `utils.templatetags.sidebar_extras`. No per-model wiring is needed; setting the attribute on the admin is sufficient.

### 7.3 Changeform actions and copy-link buttons

Use Unfold-native button patterns everywhere; **custom-inject a button only for copy links**, which the Clipboard API forces to be a real `<button>` on the same page (a server-side action cannot copy).

- **Server actions** → declare them in `actions_detail` (change-form header) or `actions_row` (changelist rows) with `@action(description=..., url_path=..., permissions=[...])`. Conditional visibility is enforced only when `permissions=[...]` is passed, which wires the `has_<action>_permission` method.
- **Copy-link buttons** → the only exception. Inject `copy_button_extra_attrs` (a `mark_safe` attribute string: `type="button" data-copy-url="<url>"`) from a `change_view` override, then render the button in an `object-tools-items` override through `{% component "unfold/components/button.html" %}` with `extra_attrs=copy_button_extra_attrs`. `static/js/copy_clipboard.js` (loaded via the admin's `Media`) wires the click-to-copy.

Both the Artist subscription buttons (`artworks/admin.py` + `admin/artworks/artist/change_form.html`) and the blog image copy button (`blog/admin.py` + `admin/blog/blogimage/change_form.html`) follow this pattern. See [[django-image-copy-link|Image Copy Link]].

## 8. Layout Constraints

To ensure the "bottom bar" (sticky action buttons) and responsive containers work correctly:
- **Inheritance**: Do not extend `unfold/layouts/base.html` in your `base.html` overrides; always extend `admin/base.html`.
- **Custom CSS**: Avoid applying `position: absolute` or `position: fixed` to the main page containers (`#page`, `#main`, etc.), as this interferes with Unfold's native sticky positioning logic.
- **Admin Base**: Use `ModelAdminUnfoldBase` for all application models to ensure consistent button availability and unsaved form warnings.
```
