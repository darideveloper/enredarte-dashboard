## ADDED Requirements

### Requirement: Translation inlines always show exactly two languages
Every translation inline in the Django admin (Artist, ArtCurator, Discipline, Technique, Theme, Format, Scale, Gallery, Location, Artwork) SHALL support exactly two translation rows: Spanish (`es`) and English (`en`).

#### Scenario: New parent object shows two translation rows
- **WHEN** an admin creates a new Artist, ArtCurator, Discipline, Technique, Theme, Format, Scale, Gallery, Location, or Artwork
- **THEN** the translation inline shows two rows pre-filled with languages `es` and `en`

#### Scenario: Existing parent with missing translations still shows both rows
- **WHEN** an admin opens an existing parent object that has zero or one translation rows
- **THEN** the translation inline shows extra rows for the missing languages, so the editor can fill both `es` and `en`

#### Scenario: No more than two translation rows can be added
- **WHEN** an admin attempts to add a third translation row to a parent that already has both `es` and `en`
- **THEN** the admin does not allow more than two translation rows

### Requirement: Translation rows cannot be deleted
Translation inline rows SHALL NOT be removable from the admin, so a parent can never lose one of its two languages.

#### Scenario: No delete control on translation rows
- **WHEN** an admin views any translation inline
- **THEN** no per-row delete checkbox or delete action is rendered for translation rows

### Requirement: Saving requires both languages to be filled
The admin SHALL reject saving a parent object unless both the Spanish and English translation rows are present, are not marked for deletion, and will actually be persisted — even when the translation inline was left completely untouched.

#### Scenario: Saving with both languages filled succeeds
- **WHEN** an admin fills both the Spanish and English translation rows and saves
- **THEN** the parent object and its two translations are saved successfully

#### Scenario: Saving with one language missing is rejected
- **WHEN** an admin leaves the English translation row blank and attempts to save
- **THEN** the admin shows a validation error and does not save the parent object

#### Scenario: Saving with the translation inline left untouched is rejected
- **WHEN** an admin creates a parent object and saves without filling any translation row
- **THEN** the admin shows a validation error requiring both `es` and `en` translations before saving, even though the inline was not edited

#### Scenario: Legacy data missing a language is rejected until completed
- **WHEN** an admin edits a legacy parent object that has zero or one translation rows and saves without completing both
- **THEN** the admin shows a validation error requiring both `es` and `en` translations before saving

### Requirement: Translation inline editor behavior is defined once
The shared translation inline behavior (formset, language pre-fill, `clean()` enforcement, `can_delete`, `min_num`, `max_num`, `get_extra`, verbose names) SHALL be implemented in a single shared base inline class used by all ten translation inlines.

#### Scenario: All translation inlines share one base class
- **WHEN** any translation inline is inspected in the admin source
- **THEN** it subclasses the shared `TranslationInline` base and only defines its `model` and `fields`

#### Scenario: Behavior change applies to all translation inlines
- **WHEN** the shared base inline behavior is changed
- **THEN** all ten translation inlines reflect the change without per-inline edits
