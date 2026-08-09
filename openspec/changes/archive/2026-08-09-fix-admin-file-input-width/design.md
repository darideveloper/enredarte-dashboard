## Context

The Django admin is themed with **Unfold**. Unfold renders file/image inputs as a decorated flex container holding a hidden real `<input type="file">` plus a fake, disabled `<input type="text">` that shows the filename or the "Seleccionar archivo para subir" placeholder. Both widget templates — `clearable_file_input.html` (large, with image preview) and `clearable_file_input_small.html` (used in inlines) — mark this fake input with classes `grow font-medium min-w-0 px-3 py-2 text-ellipsis` but never set a width. Because `flex-grow` on an input is not enough to override its intrinsic `size`-based width in this context, long text is truncated by `text-ellipsis`, so the label is not fully visible.

The project already loads a global admin stylesheet, `static/css/style.css`, on every admin page through `project/templates/admin/base.html` (`{% static 'css/style.css' %}`). `STATICFILES_DIRS` includes the `static/` folder.

## Goals / Non-Goals

**Goals:**
- Make the fake filename input fill the widget width so the label is fully visible in change forms and inlines.
- One shared, maintainable fix that covers every file input in every admin.
- Keep the fix robust against translation changes (not keyed on `aria-label` text).

**Non-Goals:**
- No changes to Unfold's Python widgets or templates.
- No per-field Python wiring (`formfield_overrides`, widget subclassing) for this cosmetic issue.
- No restyle of any other admin input.

## Decisions

**Decision 1: CSS-only fix in `static/css/style.css`.**
Append:
```css
label.grow.relative {
    display: flex;
}
```
- Rationale: the fake input already carries Unfold's `grow` (`flex-grow: 1`) and `min-w-0` (`min-width: 0`) Tailwind classes, but they are inert because the wrapping `<label class="grow relative">` is not a flex container. Turning the label into a flex container activates `flex-grow`, so the input fills the label width and the placeholder text is fully visible. Minimal footprint, zero new dependencies, single rule, and the stylesheet is already loaded globally. Verified in `venv/lib/python3.12/site-packages/unfold/templates/` that `label.grow.relative` occurs only in the two file-input widget templates (the other `grow relative` element, in `fieldset_row_field.html`, is a `<div>`, excluded by the `label` prefix). This rule is also i18n-independent (not keyed on `aria-label` text).
- Alternative rejected — `width: 100%` on the input: verified in the browser that this fixes the large widget (change-form `ImageField`) but **regresses the small inline widget**: percentage width against a content-driven flex item triggers a circular flex sizing that collapses the label to the input's min-content (e.g. 243px → 153px) and truncates the label text. `display: flex` avoids the percentage/circular resolution entirely.
- Alternative rejected: subclass Unfold's file widgets and set `formfield_overrides` on `ModelAdminUnfoldBase`. Works, but must be hand-merged with Unfold's `FORMFIELD_OVERRIDES` and duplicated for `FORMFIELD_OVERRIDES_INLINE`; more code for the same visual result.
- Alternative rejected: copy Unfold's two widget templates into `project/templates/unfold/widgets/` and add a class. Follows an existing project pattern, but duplicates ~90 lines of template markup and drifts on Unfold upgrades.

**Decision 2: `display: flex` on the label rather than a width property on the input.**
Setting a plain CSS `width: 100%` on the input reproduces the reporter's inline-style fix but fails on the small inline widget (see Decision 1). Making the label a flex container reuses the widget's existing `grow`/`min-w-0` classes, works regardless of Unfold's Tailwind pipeline, and was verified in the browser to fix the large widget while leaving the small widget untouched.

## Risks / Trade-offs

- **Selector coupling to Unfold internals** → Mitigated by relying on structural classes that are already stable across both widget templates; the rule degrades harmlessly if Unfold renames them.
- **Unfold upgrade could change markup** → The fix is two lines; if the widget structure changes, the selector simply stops matching and the file inputs revert to current (unfixed) behavior — easy to detect and update.
- **False-positive styling of unrelated disabled text inputs** → Mitigated by the `label.grow.relative` scope, which exists only in file-input widgets; no other admin input matches.
