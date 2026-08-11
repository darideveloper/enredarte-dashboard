## ADDED Requirements

### Requirement: Code fences enclose code only
Code samples in the docs SHALL be fully enclosed in fenced code blocks; explanatory prose SHALL NOT be placed inside a code fence, and no prose SHALL be left orphaned immediately after a closing fence where it reads as code.

#### Scenario: Orphaned sentence fixed in unfold guide
- **WHEN** a reader follows `docs/django-unfold-admin.md` §3.1
- **THEN** the sentence "No `permission` callback, no Python helper, no custom `AdminSite` subclass, and no `core/admin.py` changes are required." SHALL be moved inside the code block as a comment (not left orphaned after the closing fence)

### Requirement: Consistent wiki-link format
Links to documents inside `docs/` SHALL use short-form wiki links (`[[django-project-setup|Project Setup Guide]]`); links to resources outside the folder (external vault refs such as `30-resources/*`) SHALL NOT remain as vault-path wikilinks — they become plain text labels (e.g. `Redis (external)`).

#### Scenario: Redis guide links normalized
- **WHEN** a reader follows `docs/django-redis.md`
- **THEN** links to docs in this folder SHALL use short-form `[[name|label]]`, and links to external vault resources SHALL be plain text labels rather than vault-path wikilinks
