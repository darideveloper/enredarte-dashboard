## ADDED Requirements

### Requirement: Gallery has a primary flag
The `Gallery` model SHALL have an `is_primary` boolean field that defaults to `False`. It SHALL identify the single main gallery of the collection.

#### Scenario: Default is not primary
- **WHEN** a `Gallery` is created without specifying `is_primary`
- **THEN** the gallery's `is_primary` SHALL be `False`.

#### Scenario: Marking a gallery as primary
- **WHEN** a `Gallery` is saved with `is_primary=True`
- **THEN** the gallery's `is_primary` SHALL be `True`.

### Requirement: Only one primary gallery exists
The system SHALL ensure that `is_primary` is unique across the whole backend: at most one `Gallery` SHALL have `is_primary=True` at any time, active or not. Uniqueness SHALL be enforced by a database-level conditional unique constraint on `is_primary` (`condition=Q(is_primary=True)`), so the database rejects a second primary regardless of how the write occurs. When a gallery is saved as primary through the ORM, all other galleries SHALL have their `is_primary` set to `False`.

#### Scenario: Flagging a second gallery un-flags the first
- **GIVEN** a gallery `A` has `is_primary=True`
- **WHEN** a gallery `B` is saved with `is_primary=True`
- **THEN** `A.is_primary` SHALL become `False`
- **AND** `B.is_primary` SHALL be `True`.

#### Scenario: Database rejects a second primary
- **GIVEN** an active gallery has `is_primary=True`
- **WHEN** a second gallery is written with `is_primary=True` bypassing the ORM save override
- **THEN** the database SHALL reject the write (e.g. with an `IntegrityError`).

### Requirement: Primary flag exposed in the API serializer
The `GallerySerializer` SHALL include the `is_primary` field so the frontend can read it from both the gallery list and detail endpoints.

#### Scenario: Gallery API includes is_primary
- **WHEN** a gallery is serialized by `GallerySerializer`
- **THEN** the response SHALL contain the `is_primary` boolean.
