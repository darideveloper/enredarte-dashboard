## ADDED Requirements

### Requirement: Unfold app registration
The system SHALL register `unfold`, `unfold.contrib.filters`, `unfold.contrib.forms`, and `unfold.contrib.inlines` in `INSTALLED_APPS` BEFORE `django.contrib.admin`. This ensures Unfold's templates and static files override Django's built-in admin.

#### Scenario: Unfold takes priority
- **WHEN** the Django admin is accessed
- **THEN** Unfold's modern UI SHALL render instead of Django's classic admin

### Requirement: UNFOLD settings dictionary
The system SHALL define an `UNFOLD` settings dictionary with: `SITE_TITLE="Enredarte Admin"`, `SITE_HEADER="Enredarte"`, `SITE_SUBHEADER="Panel de Administracion"`, `SITE_URL="/"`, `SITE_SYMBOL="palette"`, `SHOW_HISTORY=True`, `SHOW_VIEW_ON_SITE=True`, `THEME="light"`, and a purple OKLCH color palette matching the documented primary color ramp (50-950).

#### Scenario: Admin header shows Spanish title
- **WHEN** a user visits `/admin/`
- **THEN** the sidebar SHALL display "Enredarte Admin" as the site title, "Enredarte" as header, and "Panel de Administracion" as subheader

#### Scenario: OKLCH colors applied
- **WHEN** the admin theme renders
- **THEN** all primary-colored elements SHALL use the OKLCH purple palette centered at hue 296

### Requirement: Environment callback
The system SHALL create `utils/callbacks.py` with an `environment_callback` function that maps `ENV` values (`prod`, `staging`, `dev`, `local`) to colored badge labels in the admin header (`["Produccion", "danger"]`, `["Staging", "warning"]`, `["Desarrollo", "info"]`, `["Local", "success"]`).

#### Scenario: Dev environment badge
- **WHEN** `ENV=dev` and the admin is loaded
- **THEN** a blue "Desarrollo" badge SHALL appear in the admin header

### Requirement: Auth model admin with Unfold forms
The system SHALL create `project/admin.py` that unregisters and re-registers `User` and `Group` models using Unfold's custom forms (`UserChangeForm`, `UserCreationForm`, `AdminPasswordChangeForm` from `unfold.forms`). Both `UserAdmin` and `GroupAdmin` SHALL inherit from `BaseUserAdmin`/`BaseGroupAdmin` AND `ModelAdminUnfoldBase` (from `project.admin_base`), not raw `ModelAdmin`, to inherit `sidebar_icon`, `compressed_fields`, `warn_unsaved_form`, `list_filter_sheet`, `change_form_show_cancel_button`, and the `edit` row action. All admin model registrations SHALL be placed in the app-level `admin.py` files (e.g., `artworks/admin.py` for future models, `project/admin.py` for contrib auth).

> **DRF-only**: `TokenAdmin`/`TokenProxy` (from `rest_framework.authtoken`) are only required if the project uses DRF's `TokenAuthentication`. If included, `TokenProxy` SHALL be unregistered and re-registered with `@admin.register(TokenProxy)` and `TokenAdmin(BaseTokenAdmin)` with `sidebar_icon="key"`.

#### Scenario: User creation uses Unfold form
- **WHEN** admin clicks "Add User" in the admin
- **THEN** the creation form SHALL use Unfold-styled fields and widgets

### Requirement: ModelAdminUnfoldBase base class
The system SHALL create `project/admin_base.py` with a `ModelAdminUnfoldBase` class that extends `unfold.admin.ModelAdmin` with: `compressed_fields=True`, `warn_unsaved_form=True`, `list_filter_sheet=False`, `change_form_show_cancel_button=True`, `actions_row=["edit"]`, and a default `sidebar_icon="database"`. It SHALL include an `edit` row action decorated with `@action(description="Edit", permissions=["change"])` that redirects to the model's change view.

#### Scenario: Row actions appear in change list
- **WHEN** a model admin using `ModelAdminUnfoldBase` renders its change list
- **THEN** each row SHALL show an "Editar" action button linking to the change form

#### Scenario: Unsaved form warning
- **WHEN** a user modifies a form and tries to navigate away
- **THEN** the browser SHALL warn that unsaved changes will be lost

### Requirement: Permission-aware auto sidebar
The system SHALL configure the sidebar with `show_all_applications: True` and empty `navigation: []`, and override `project/templates/unfold/helpers/navigation.html` to iterate `available_apps` (Django's permission-filtered app list) using Unfold-styled DOM. The template SHALL mark the active model based on request path match and fall back to an error partial for users with no admin permissions.

#### Scenario: Registered models auto-appear
- **WHEN** a `ModelAdmin` is registered and the user has view permissions
- **THEN** the model SHALL appear in the sidebar without any `UNFOLD` settings change

#### Scenario: No permission means no sidebar entry
- **WHEN** a user lacks view permission for a model
- **THEN** that model SHALL NOT appear in the sidebar

### Requirement: Sidebar icon mapping infrastructure
The system SHALL provide three files for the sidebar icon pipeline:
- `utils/admin_icons.py` with `build_sidebar_icon_map()` that introspects `admin.site._registry` for `sidebar_icon` attributes and returns `{app_label.model_name: icon_name}` dict
- `utils/context_processors.py` with `user_palette(request)` that injects `sidebar_icons` (and `user_palette_css` as empty string) into every template context, and SHALL be registered in `TEMPLATES[0]["OPTIONS"]["context_processors"]`
- `utils/templatetags/sidebar_extras.py` with a `get_item` template filter for dictionary lookups, registered as `sidebar_extras` in `TEMPLATES[0]["OPTIONS"]["libraries"]`

#### Scenario: Per-model icon shown in sidebar
- **WHEN** a `ModelAdmin` defines `sidebar_icon = "palette"`
- **THEN** the sidebar navigation template SHALL render the "palette" Material icon next to that model's link via `sidebar_icons|get_item:model_key|default:"database"`

#### Scenario: Context processor injects icon map
- **WHEN** any admin page renders
- **THEN** the `sidebar_icons` context variable SHALL be available in the template

### Requirement: Admin base template override
The system SHALL create `project/templates/admin/base.html` extending `"admin/base.html"` (never `unfold/layouts/base.html`) that loads SimpleMDE CSS/JS from CDN, `static/css/style.css`, and three custom JS files: `add_tailwind_styles.js`, `load_markdown.js`, and `range_date_filter_es.js`. The `{{ block.super }}` call SHALL preserve upstream Unfold assets in the `extrahead` block.

#### Scenario: SimpleMDE available in admin
- **WHEN** a textarea is present on any admin form page
- **THEN** SimpleMDE SHALL be loaded and available for initialization by `load_markdown.js`

#### Scenario: Unfold layout preserved
- **WHEN** the admin page renders
- **THEN** Unfold's sticky bottom bar and responsive layout SHALL work correctly (not broken by overriding the internal layout directly)

### Requirement: Tailwind style injection
The system SHALL create `static/js/add_tailwind_styles.js` that, on `DOMContentLoaded`, adds Tailwind utility classes to Unfold elements: `.btn` elements receive full width, padding, rounded corners, and primary color backgrounds; `.img-preview` elements receive auto width, 4rem height, rounded-xl, and object-cover.

#### Scenario: Buttons styled
- **WHEN** the admin page finishes loading
- **THEN** all `.btn` elements SHALL have Tailwind classes for consistent styling

### Requirement: SimpleMDE markdown integration
The system SHALL create `static/js/load_markdown.js` that, on `DOMContentLoaded`, initializes SimpleMDE on all textareas (`div > textarea` selector) with a toolbar containing: bold, italic, heading, quote, code, link, image, unordered-list, ordered-list, undo, redo, preview. Initialization SHALL be delayed by 100ms via `setTimeout`.

#### Scenario: Textarea gets markdown editor
- **WHEN** an admin form page with a textarea loads
- **THEN** the textarea SHALL be replaced by a SimpleMDE markdown editor with the configured toolbar

### Requirement: Spanish date range filter placeholders
The system SHALL create `static/js/range_date_filter_es.js` that, on `DOMContentLoaded`, sets Spanish placeholder text on Unfold's range date filter inputs: `created_at_from` and `updated_at_from` → "Desde", `created_at_to` and `updated_at_to` → "Hasta".

#### Scenario: Spanish date placeholders
- **WHEN** a model change list with date range filters renders
- **THEN** the "from" date input SHALL show "Desde" and the "to" input SHALL show "Hasta" as placeholders

### Requirement: Markdown preview CSS
The system SHALL create `static/css/style.css` with comprehensive `.editor-preview` and `.editor-preview-side` typography styles: headings (h1-h3) with proper sizing and border-bottom separators, paragraphs with bottom margin, unordered and ordered lists with bullet/number styles and padding, blockquotes with left border and italic styling, inline code with background and monospace font, code blocks with background and padding, and links with primary color and underline.

#### Scenario: Markdown preview readable
- **WHEN** SimpleMDE renders a markdown preview
- **THEN** headings, lists, code blocks, and blockquotes SHALL be visually distinct using Unfold's CSS variables

### Requirement: Site branding assets
The system SHALL create `static/logo.webp` and `static/favicon.png` as placeholder files. The `UNFOLD` dict SHALL reference `SITE_LOGO` as `lambda request: static("logo.webp")` and `SITE_ICON` as `lambda request: static("favicon.png")`. `SITE_FAVICONS` SHALL include a 32x32 PNG icon referencing `static("favicon.png")`.

#### Scenario: Logo and favicon display
- **WHEN** the admin sidebar renders
- **THEN** the placeholder logo SHALL appear in the sidebar and the favicon SHALL appear in the browser tab

### Requirement: Navigation user template override
The system SHALL create `project/templates/unfold/helpers/navigation_user.html` as a replacement for Unfold's bundled version, rendering user avatar, full name, and email at the bottom of the sidebar with Alpine.js interactions for theme/language switches and account links.

#### Scenario: User info in sidebar
- **WHEN** an authenticated admin user views the sidebar
- **THEN** their full name, email, and avatar SHALL be displayed at the bottom of the sidebar

### Requirement: Spanish text in sidebar navigation
The system SHALL ensure that when the auto sidebar renders app labels and model names from Django's `available_apps`, the default Django app labels (Auth → "Autenticacion y autorizacion", Users → "Usuarios", Groups → "Grupos") are displayed. All custom model verbose names and app config verbose names SHALL be defined in Spanish.

#### Scenario: App labels in Spanish
- **WHEN** the sidebar renders `available_apps`
- **THEN** app and model names SHALL appear in Spanish (e.g., "Autenticacion y autorizacion" not "Authentication and Authorization")
