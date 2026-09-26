## ADDED Requirements

### Requirement: Inline social links management for ArtCurator
The system SHALL expose `ArtCuratorSocialLink` as a `TabularInline` named `ArtCuratorSocialLinkInline` on `ArtCuratorAdmin` with fields `platform` and `url`. The inline SHALL render under translation inlines, allow adding and removing links without leaving the curator edit page, and SHALL NOT use `sort_order`-based ordering.

#### Scenario: Editing links on the curator form
- **WHEN** an administrator opens an ArtCurator edit form
- **THEN** they can view, add, modify, and delete the curator's social links directly in the inline formset without navigating away.

#### Scenario: Curator admin form saves without social links
- **WHEN** an administrator saves an ArtCurator form with no social links filled in
- **THEN** the curator is saved successfully without error.
