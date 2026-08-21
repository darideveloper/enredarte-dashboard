## ADDED Requirements

### Requirement: Hub indexes all documents in docs/
The `docs/django.md` hub SHALL list every markdown document stored in the same `docs/` folder as an internal resource link, so no document is orphaned from the note graph.

#### Scenario: Hub lists all docs
- **WHEN** a user reads the Internal Resources section of `docs/django.md`
- **THEN** it SHALL include links to `django-project-setup`, `django-model-definitions`, `django-media-storage`, `django-unfold-admin`, `django-image-copy-link`, `django-drf`, `django-fixtures`, `django-redis`, `django-local-subdomain-setup`, and `django-i18n-es-admin`

#### Scenario: New document added later
- **WHEN** a new `django-*.md` document is added to `docs/` in the future
- **THEN** it SHALL also be added to the hub's Internal Resources list

### Requirement: Wikilink portability convention documented in hub
The `docs/django.md` hub SHALL include a section documenting how agents converting the docs to a new Django project SHALL handle Obsidian wikilinks: short-form links to sibling docs stay as-is, vault-path links to sibling docs convert to short-form, and external `30-resources/*` links become plain text labels.

#### Scenario: Agent reads the convention
- **WHEN** an agent copies `docs/` into a new Django project and reads `docs/django.md`
- **THEN** it SHALL find instructions to convert external vault-path wikilinks to plain text labels and to convert vault-path sibling links to short-form `[[name|label]]`
