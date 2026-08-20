## Context

The Django Admin renders two image previews, both in `artworks/admin.py`:

- `ArtworkAdmin.display_image` (changelist list column): a 40px square thumbnail of the primary `ArtworkImage`.
- `ArtworkImageInline.display_preview` (readonly field inside the `ArtworkImage` TabularInline): a 50px thumbnail.

Both currently emit `<img ... class="img-preview" style="height:...; border-radius:...; object-fit:...">`, duplicating sizing between inline styles and the `img-preview` class. `static/js/add_tailwind_styles.js` injects Tailwind classes (`w-auto h-16 rounded-xl object-cover`) onto `.img-preview` on `DOMContentLoaded`, but inline styles win in CSS specificity, so the injected classes are effectively dead for these elements and a JS dependency is introduced for styling that should live in CSS.

## Goals / Non-Goals

**Goals:**
- Make `.img-preview` a real CSS class in `static/css/style.css` — the single source of truth for preview size and shape.
- Remove all inline `style=` attributes from the two preview renderers.
- Remove the `.img-preview` Tailwind-injection entry from `add_tailwind_styles.js`.
- Provide three size variants as real CSS: base `.img-preview` (regular, 50px), `.img-preview--sm` (small, 40px square for the list), and `.img-preview--lg` (large).
- Update `docs/django-unfold-admin.md` to match the implemented convention.

**Non-Goals:**
- Not changing the `copy_link` / image clipboard feature.
- Not altering Unfold's built-in file-upload widget styling (`admin-file-input` capability is out of scope).
- No new dependencies, no model/migration changes, no templates touched.

## Decisions

**Decision 1: Move `.img-preview` styling to real CSS in `static/css/style.css`.**
- *Rationale*: Eliminates the JS-injection mechanism and the CSS-specificity conflict (inline beats class). Styling becomes reliable even if JS fails and is centrally editable. Aligns with the project's existing `static/css/style.css` which already holds Unfold-specific overrides.
- *Alternatives considered*: Keeping JS injection (rejected: fragile, dead classes, adds a runtime dependency for pure presentation).

**Decision 2: Base class + size variants (`--sm`, `--lg`) instead of independent classes.**
- Base `.img-preview`: `height: 50px; border-radius: 6px; object-fit: cover;` (regular, matches the current inline preview default).
- `.img-preview--sm`: `height: 40px; width: 40px; object-fit: cover;` (small square, matches the current list thumbnail).
- `.img-preview--lg`: `height: 64px; width: 64px; object-fit: cover;` (large square, for larger previews where needed).
- *Rationale*: One shared rule with size modifiers mirrors a BEM-ish convention, supports regular/small/large sizes, and avoids duplicating the base shape rules.
- *Alternatives considered*: Single uniform size for all (rejected: loses the intentionally distinct sizes); fully separate classes per context (rejected: more duplication).

**Decision 3: Remove the `.img-preview` entry from `add_tailwind_styles.js`.**
- *Rationale*: Dead code once CSS owns the styling; the selector no longer needs JS. The `.btn` entry stays untouched.

**Decision 4: Docs state the class-based convention.**
- *Rationale*: `docs/django-unfold-admin.md` currently documents `.img-preview` as JS-injected; it must be updated to describe the CSS class so future admin code follows the same pattern (emit `class="img-preview"` with no inline styles).

## Risks / Trade-offs

- **[CSS loads but JS-based Unfold enhancements still needed]** → `.btn` remains JS-injected; only the image-preview entry is removed, so the script still runs for buttons. No regression.
- **[Future previews forget the variant]** → The `--sm`/`--lg` modifiers and inline-style-free pattern are documented in the docs; default `.img-preview` (regular) size applies if a variant is omitted, which is acceptable.
- **[Sizing differences between environments]** → Sizes are hardcoded px in `style.css`; consistent across list and inline as defined. No responsive concerns for admin thumbnails.
