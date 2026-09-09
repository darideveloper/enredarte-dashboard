---
created: 2026-09-09
updated: 2026-09-09
tags:
  - enredarte
  - fixtures
  - env
type: guide
status: active
---

# Enredarte Fixtures & Environments

Live fixture inventory and the base-vs-seed lifecycle. Pattern details: [[django-fixtures\|Fixed Data Loading with Django Fixtures]].

## Lifecycle

| Tier | Command | When | Scope |
|---|---|---|---|
| Base | `base_loaddata` | Always: every deploy (`start.sh`), every new env, tests | `artworks/fixtures/artworks/*.json` |
| Seed | `seed_loaddata` | Once, manually, per env wanting demo data | `*/fixtures/*/seed/*.json` (+ `seed/images/` sync) |

`FIXTURE_DIRS` in `project/settings.py` points at `artworks/fixtures/artworks` only; blog fixtures resolve via app-directory discovery. Loaders live in `core/management/commands/` and auto-discover every installed app.

## Live inventory

Artworks base (`artworks/fixtures/artworks/*.json`, always loaded):

- `Discipline`, `DisciplineTranslation`, `Format`, `FormatTranslation`, `Location`, `LocationTranslation`, `Scale`, `ScaleTranslation`, `Technique`, `TechniqueTranslation`, `Theme`, `ThemeTranslation`

Artworks seed (`artworks/fixtures/artworks/seed/`, numeric order, once):

- `00_ArtCurator`, `01_ArtCuratorTranslation`, `02_Artist`, `03_ArtistSocialLink`, `04_ArtistTranslation`, `05_Artwork`, `06_Gallery`, `07_GalleryTranslation`, `08_ArtworkGallery`, `09_ArtworkImage`, `10_ArtworkTranslation`

Blog seed (`blog/fixtures/blog/seed/`, once):

- `00_Post`, `01_PostTranslation`, `02_BlogImage`

Core and subscriptions ship no fixtures.

## Rules

- Seed rows may reference base PKs — always run `base_loaddata` first.
- Within an app, files load alphabetically; numeric prefixes enforce FK order.
- Re-running updates rows in place (explicit PKs); `seed_loaddata` re-runs are harmless but never belong in `start.sh` or CI.
- Tests: `call_command("base_loaddata")` in `setUp`; add seed only for tests needing demo rows.

## See also

- [[enredarte-overview\|Enredarte Overview]]
- [[enredarte-deploy\|Enredarte Deploy]] (where `base_loaddata` runs)
