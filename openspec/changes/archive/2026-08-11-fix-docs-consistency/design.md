## Context

The `docs/` folder is the project's source of truth for Django setup and conventions. A full audit surfaced 16 findings spanning cross-document conflicts (hub index, storage settings, docker ARGs, entrypoint, admin wiring, project naming, logo, Spanish JS) and per-file issues (code-fence boundary, wiki-link format, model choices idiom). Two findings (12, 13) were withdrawn after the user confirmed the referenced files resolve via an external Obsidian vault at `/home/daridev/Desktop/obsidian/daridev/20-areas/work` — no action needed there.

All fixes are documentation-only. No code, models, migrations, or runtime behavior change.

## Goals / Non-Goals

**Goals:**
- Make `django.md` index every document in the folder.
- Make setup/storage/deploy/admin docs agree so a reader following them verbatim gets a working project.
- Eliminate duplicate `project/admin.py` code and divergent naming/formats.
- Preserve the docs' portability: sample domains stay generic, English remains the default (Spanish handled by `django-i18n-es-admin.md`).

**Non-Goals:**
- Auditing or changing the actual codebase (per explicit user instruction, docs only).
- Adding a custom translation catalog or touching i18n beyond moving the `range_date_filter_es.js` reference.
- Renaming the `project` package to anything else.

## Decisions

### D1 — Hub gets all 4 missing links
`django.md` currently links 6 docs + a mermaid note; it misses `django-fixtures`, `django-redis`, `django-local-subdomain-setup`, `django-i18n-es-admin`. Add all four to the Internal Resources list.
- *Alternative considered*: only add Django-specific ones, or replace the list with a generic pointer. Rejected: the user chose "add all 4"; a complete list keeps the note graph self-describing with minimal maintenance.

### D2 — Storage location vars + cross-reference
Add the three `*_LOCATION` assignments in the S3 branch of `django-project-setup.md` Step 7 (matching `django-media-storage.md`) and a one-line cross-reference to the full storage guide.
- *Rationale*: without these, `storage_backends.py` fails with `AttributeError`; cross-ref keeps duplication low.

### D3 — Private backend in local STORAGES fallback
Add a `private` entry (`FileSystemStorage`) under a `private-media/` subfolder of `MEDIA_ROOT` to the local fallback.
- *Alternative considered*: remove `private` from both branches (YAGNI). Rejected: user chose to add it; keeps S3/local parity.

### D4 — Complete Docker ARG list in media-storage
Add `AWS_S3_REGION_NAME`, `AWS_S3_CUSTOM_DOMAIN`, `AWS_PROJECT_FOLDER` to the Docker snippet in `django-media-storage.md` so it matches `django-project-setup.md` §14.
- *Rationale*: the media-storage guide is often read standalone; a partial ARG list would silently omit settings used by the very storage classes it defines.

### D5 — base_loaddata in start.sh
Insert `python manage.py base_loaddata` after `migrate` with a comment ("base data is required for the system to work"), honoring the `django-fixtures.md` contract. Only base, never seed.
- *Alternative considered*: conditional guard or commented placeholder. Rejected: user chose the direct call; fixtures doc already explains the base/seed split.

### D6 — makemigrations --check in start.sh + pre-deploy note
Change `makemigrations --noinput` → `makemigrations --check --noinput` so the entrypoint validates (fails loudly if migrations missing) instead of generating files at runtime. Add a note: run `makemigrations` locally before building the image and commit the files.
- *Rationale*: generated migrations at deploy time are non-deterministic and can produce drift; validating keeps the guarantee without runtime generation.

### D7 — Explicit `import project.admin`
Add `import project.admin` to the `urls.py` template with a comment. This is a documented Django gotcha (project package not in `INSTALLED_APPS` → admin not auto-discovered).
- *Rationale*: silently missing customizations (sidebar icons, Unfold forms) are a common failure; the comment preserves the rationale.

### D8 — Single canonical copy of project/admin.py
Keep the full block only in `django-unfold-admin.md` §7.1; in `django-project-setup.md` Step 10 replace the code with a pointer to §7.1.
- *Rationale*: eliminates drift between two near-identical copies. Alternative of splitting content across both docs rejected — the code is Unfold-specific and belongs with the Unfold guide.

### D9 — Rename myproject → project in drf.md
Global rename in `django-drf.md`, plus the sample model's `LANGS` dict → `models.TextChoices`.
- *Rationale*: matches `django-project-setup.md` exactly; `TextChoices` is the modern idiom and avoids the dict-as-choices antipattern.

### D10 — Spanish JS belongs in the Spanish recipe
Remove `range_date_filter_es.js` from the default `admin/base.html` in `django-project-setup.md`; document it in `django-i18n-es-admin.md`.
- *Rationale*: default language is English; Spanish-only assets in the base template are noise. Keeps the i18n recipe self-contained.

### D11 — Logo filename aligned to logo.webp
`django-project-setup.md` Step 11 → `logo.webp`.
- *Rationale*: matches `django-unfold-admin.md` `SITE_LOGO` reference. Alternative (svg) rejected by user.

### D12 — Code-fence and wiki-link formatting
Move the orphaned §3.1 sentence inside the code block as a comment; normalize `django-redis.md` links: short-form for in-folder docs, plain text labels for external vault refs.
- *Rationale*: consistency with the rest of the folder; external vault refs are replaced with plain text labels so the docs read cleanly outside the vault.

### D13 — Wikilink portability convention in hub
Add a section at the bottom of `docs/django.md` documenting how `[[wikilinks]]` must be handled when copying docs into a new Django project. Rules: short-form sibling links stay as-is, vault-path sibling links convert to short-form, external `30-resources/*` links become plain text labels.
- *Rationale*: the docs live in two contexts (full Obsidian vault + per-project copies). Team members without the vault would see broken wikilinks; an explicit convention tells the agent how to make a project copy self-contained.

## Risks / Trade-offs

- **Silent divergence between docs** → Mitigation: `project/admin.py` is canonicalized in one place (D8); cross-references (D2, D8) point readers at the source of truth.
- **Docs still get out of sync later** → Mitigation: specs in this change codify the invariants (hub completeness, single-copy admin code, ARG parity); they serve as a checklist for future edits.
- **`makemigrations --check` blocks deploys if a developer forgets to commit migrations** → Mitigation: that is the intended loud failure; the pre-deploy note documents the fix.
- **Moving the Spanish JS changes the English setup's template** → Mitigation: the default project is English; the Spanish recipe fully documents where the script belongs.
- **External wikilinks break when docs are copied into a new project** → Mitigation: the hub documents the wikilink portability convention (D13) so agents convert external vault-path refs to plain text labels and sibling vault-path refs to short-form on copy.

## Migration Plan

None — no runtime deployment. Artifacts are Markdown edits; apply in place and verify by re-reading each edited section.

## Open Questions

None.
