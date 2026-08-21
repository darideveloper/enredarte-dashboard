## 1. Core model base labels

- [x] 1.1 Add Spanish `verbose_name` to `TimeStampedModel` fields in `core/models.py`: `created_at` → "Creado el", `updated_at` → "Actualizado el"
- [x] 1.2 Add Spanish `verbose_name` to `BaseModel` fields in `core/models.py`: `slug` → "Slug", `is_active` → "Activo", `sort_order` → "Orden"
- [x] 1.3 Add Spanish `verbose_name` to `TranslationBase` in `core/models.py`: `language` → "Idioma"
- [x] 1.4 Add Spanish `verbose_name` to `Person` fields in `core/models.py`: `name` → "Nombre", `email` → "Correo electrónico", `website` → "Sitio web", `photo` → "Fotografía"

## 2. Artworks model labels

- [x] 2.1 Add `Meta.verbose_name`/`verbose_name_plural` to `Artist` in `artworks/models.py`: "Artista"/"Artistas"
- [x] 2.2 Add Spanish `verbose_name` to `Artist` fields: `birth_year` → "Año de nacimiento", `death_year` → "Año de fallecimiento", `location` → "Ubicación"
- [x] 2.3 Add Spanish `verbose_name` to `ArtistTranslation`: `artist` → "Artista", `bio` → "Biografía"
- [x] 2.4 Add Spanish `verbose_name` to `ArtistSocialLink`: `artist` → "Artista", `platform` → "Plataforma", `url` → "URL"; change `OTHER = "other", "Other"` label to "Otra"
- [x] 2.5 Add Spanish `verbose_name` to `LocationTranslation`: `location` → "Ubicación", `name` → "Nombre"
- [x] 2.6 Add `Meta.verbose_name`/`verbose_name_plural` to `ArtCurator`: "Curador de arte"/"Curadores de arte"
- [x] 2.7 Add Spanish `verbose_name` to `ArtCuratorTranslation`: `art_curator` → "Curador de arte", `bio` → "Biografía"
- [x] 2.8 Add `Meta.verbose_name`/`verbose_name_plural` to `Gallery`: "Galería"/"Galerías"
- [x] 2.9 Add Spanish `verbose_name` to `Gallery` fields: `logo` → "Logotipo", `curator` → "Curador"
- [x] 2.10 Add Spanish `verbose_name` to `GalleryTranslation`: `gallery` → "Galería", `name` → "Nombre", `description` → "Descripción"
- [x] 2.11 Add Spanish `verbose_name` to translation FKs/names for `DisciplineTranslation` (`discipline` → "Disciplina", `name` → "Nombre"), `TechniqueTranslation` (`technique` → "Técnica"), `ThemeTranslation` (`theme` → "Temática"), `FormatTranslation` (`format` → "Tipo de pieza"), `ScaleTranslation` (`scale` → "Tamaño")
- [x] 2.12 Add `Meta.verbose_name`/`verbose_name_plural` to `Artwork`: "Obra de arte"/"Obras de arte"
- [x] 2.13 Add Spanish `verbose_name` to `Artwork` fields: `artist` → "Artista", `year` → "Año", `dimensions` → "Dimensiones", `disciplines` → "Disciplinas", `techniques` → "Técnicas", `themes` → "Temáticas", `formats` → "Tipos de pieza", `scales` → "Tamaños", `price_mxn` → "Precio (MXN)", `price_usd` → "Precio (USD)", `status` → "Estado", `is_highlighted` → "Destacada", `views_count` → "Visitas"
- [x] 2.14 Translate `ArtworkStatus` choice labels to Spanish: "Available" → "Disponible", "Sold" → "Vendida", "Reserved" → "Reservada", "On Loan" → "En préstamo", "Not Available" → "No disponible" (values unchanged)
- [x] 2.15 Add Spanish `verbose_name` to `ArtworkTranslation`: `artwork` → "Obra de arte", `title` → "Título", `description` → "Descripción"
- [x] 2.16 Add Spanish `verbose_name` to `ArtworkGallery`: `artwork` → "Obra de arte", `gallery` → "Galería", `sort_order` → "Orden"
- [x] 2.17 Add Spanish `verbose_name` to `ArtworkImage`: `artwork` → "Obra de arte", `image` → "Imagen", `alt_es` → "Texto alternativo (ES)", `alt_en` → "Texto alternativo (EN)", `is_primary` → "Imagen principal", `sort_order` → "Orden"

## 3. App configs

- [x] 3.1 Add `verbose_name = "Principal"` to `CoreConfig` in `core/apps.py`
- [x] 3.2 Add `verbose_name = "Obras"` to `ArtworksConfig` in `artworks/apps.py`

## 4. Admin definitions

- [x] 4.1 Translate fieldset titles in `artworks/admin.py` ArtistAdmin: "Personal Info" → "Datos personales", "Contact & Media" → "Contacto y medios", "System Status" → "Estado del sistema"
- [x] 4.2 Translate fieldset titles in `artworks/admin.py` ArtCuratorAdmin: "Personal Info" → "Datos personales", "Contact & Media" → "Contacto y medios", "System Status" → "Estado del sistema"
- [x] 4.3 Translate fieldset title in `artworks/admin.py` for Discipline/Technique/Theme/Format/Scale/Location admins: "System Info" → "Información del sistema"
- [x] 4.4 Translate fieldset titles in `artworks/admin.py` GalleryAdmin: "Basic Info" → "Información básica", "System Info" → "Información del sistema"
- [x] 4.5 Translate fieldset titles in `artworks/admin.py` ArtworkAdmin: "Main Attributes" → "Atributos principales", "Commercial & Status" → "Comercial y estado", "System Settings" → "Configuración del sistema"
- [x] 4.6 Change `@action(description="Edit")` to `@action(description="Editar")` in `project/admin_base.py`

## 5. Unfold Spanish catalog

- [x] 5.1 Add `LOCALE_PATHS = [BASE_DIR / "locale"]` to `project/settings.py`
- [x] 5.2 Ensure GNU `gettext` (`msgfmt`) is installed on the system (`which msgfmt`). If missing, install it (e.g. `apt-get install gettext`). The compiled `.mo` is required for Django to read translations; the `.po` alone is not enough.
- [x] 5.3 Create `locale/es/LC_MESSAGES/django.po` **by hand** (do NOT run `makemessages` — it would collect ~85 msgids from all installed-app templates including unfold's, and empty-msgstr entries would override Django's shipped catalog with blank strings). The `.po` must contain exactly these 40 msgid/msgstr pairs:

```
msgid "Search apps and models..."
msgstr "Buscar aplicaciones y modelos…"

msgid "Type to search"
msgstr "Escriba para buscar"

msgid "Nothing matched your search"
msgstr "Ningún resultado coincide con su búsqueda"

msgid "No results found"
msgstr "Sin resultados"

msgid "Recent searches"
msgstr "Búsquedas recientes"

msgid "All applications"
msgstr "Todas las aplicaciones"

msgid "Apply Filters"
msgstr "Aplicar filtros"

msgid "Reset filters"
msgstr "Restablecer filtros"

msgid "Filters"
msgstr "Filtros"

msgid "No data"
msgstr "Sin datos"

msgid "Add row"
msgstr "Agregar fila"

msgid "Select all rows"
msgstr "Seleccionar todas las filas"

msgid "Expand row"
msgstr "Expandir fila"

msgid "Run"
msgstr "Ejecutar"

msgid "After you"
msgstr "Tras"

msgid "More actions"
msgstr "Más acciones"

msgid "Select"
msgstr "Seleccionar"

msgid "Submit"
msgstr "Enviar"

msgid "Next"
msgstr "Siguiente"

msgid "Previous"
msgstr "Anterior"

msgid "Go back"
msgstr "Volver"

msgid "General"
msgstr "General"

msgid "System"
msgstr "Sistema"

msgid "Navigate"
msgstr "Navegar"

msgid "Cancel"
msgstr "Cancelar"

msgid "Click to cancel"
msgstr "Clic para cancelar"

msgid "Click to download"
msgstr "Clic para descargar"

msgid "True"
msgstr "Verdadero"

msgid "False"
msgstr "Falso"

msgid "Toggle password visibility"
msgstr "Mostrar/ocultar contraseña"

msgid "Choose file to upload"
msgstr "Seleccionar archivo para subir"

msgid "Image preview"
msgstr "Vista previa de la imagen"

msgid "Record picture"
msgstr "Capturar imagen"

msgid "Dark"
msgstr "Oscuro"

msgid "Light"
msgstr "Claro"

msgid "Forgotten your password or username?"
msgstr "¿Olvidó su contraseña o nombre de usuario?"

msgid "Return to site"
msgstr "Volver al sitio"

msgid "This item will be deleted."
msgstr "Este elemento será eliminado."

msgid "You have been successfully logged out from the administration"
msgstr "Ha cerrado sesión exitosamente del panel de administración"

msgid "This page yielded into no results. Create a new item or reset your filters."
msgstr "Esta página no generó resultados. Cree un nuevo elemento o restablezca sus filtros."
```

- [x] 5.4 Run `python manage.py compilemessages` to build `locale/es/LC_MESSAGES/django.mo`
- [x] 5.5 Verify generic Django chrome (Save/Delete/pagination/login) still resolves from Django's shipped catalog — confirm no Django-own msgids appear in the project `.po`

## 6. Migration and verification

- [x] 6.1 Run `python manage.py makemigrations` and review the generated migration (field `verbose_name` changes only; choice label edits in `ArtworkStatus` and `ArtistSocialLink.Platform` are metadata-only and do NOT produce a migration — this is expected)
- [x] 6.2 Run `python manage.py migrate`
- [x] 6.3 Run `python manage.py check` and the project test suite (`python manage.py test`)
- [x] 6.4 Restart the dev server and manually verify: model labels, model names, app names, choice badges/filters, fieldset titles, row-action button, sidebar search, filter controls, and login/confirm dialogs all render in Spanish
- [x] 6.5 Confirm DB choice values remain English (`available`, `sold`, …, `other`) and no public-site/API behavior changed
