## MODIFIED Requirements

### Requirement: Only one primary gallery exists
The system SHALL ensure that `is_primary` is unique across the whole backend: at most one `Gallery` SHALL have `is_primary=True` at any time, active or not. Uniqueness SHALL be enforced by a database-level conditional unique constraint on `is_primary` (`condition=Q(is_primary=True)`), so the database rejects a second primary regardless of how the write occurs. When a gallery is saved as primary through the ORM **or through any form-based save (such as the Django admin change/add forms)**, all other galleries SHALL have their `is_primary` set to `False` **before uniqueness is validated, so the save succeeds instead of failing constraint validation**.

#### Scenario: Flagging a second gallery un-flags the first
- **GIVEN** a gallery `A` has `is_primary=True`
- **WHEN** a gallery `B` is saved with `is_primary=True`
- **THEN** `A.is_primary` SHALL become `False`
- **AND** `B.is_primary` SHALL be `True`.

#### Scenario: Flagging a second gallery as primary through the admin form
- **GIVEN** a gallery `A` has `is_primary=True`
- **AND** an admin user opens the change form for gallery `B` and sets `is_primary=True`
- **WHEN** the form is submitted
- **THEN** the form SHALL validate successfully (no `unique_primary_gallery` constraint error)
- **AND** `A.is_primary` SHALL become `False`
- **AND** `B.is_primary` SHALL be `True`
- **AND** exactly one `Gallery` SHALL have `is_primary=True`.

#### Scenario: Flagging a new gallery as primary through the admin add form
- **GIVEN** a gallery `A` has `is_primary=True`
- **AND** an admin user creates a new gallery `B` in the admin add form with `is_primary=True`
- **WHEN** the form is submitted
- **THEN** the form SHALL validate successfully (no `unique_primary_gallery` constraint error)
- **AND** `A.is_primary` SHALL become `False`
- **AND** `B.is_primary` SHALL be `True`
- **AND** exactly one `Gallery` SHALL have `is_primary=True`.

#### Scenario: Database rejects a second primary
- **GIVEN** an active gallery has `is_primary=True`
- **WHEN** a second gallery is written with `is_primary=True` bypassing the ORM save override and form-based unflagging
- **THEN** the database SHALL reject the write (e.g. with an `IntegrityError`).