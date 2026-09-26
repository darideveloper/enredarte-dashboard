## Context

See `proposal.md` for background and motivation.

Enredarte needs to track each artist's agreed commercial commission percentage (how much of each artwork sale belongs to the artist, with the rest belonging to Enredarte). Operators manage artists, artworks, and sales orders through the Django Unfold admin. The commission is an internal operational figure, not customer-facing.

## Goals / Non-Goals

**Goals:**
- Add an integer `commission` field on `Artist` bounded between 0 and 100 with default 0.
- Show `commission` formatted (e.g. `25%`) in the `ArtistAdmin` changelist immediately adjacent to the primary columns (between Name and Email).
- Allow editing `commission` in `ArtistAdmin` change form under an "Acuerdo comercial" fieldset.
- Render read-only `display_artist_commission` in `ArtworkAdmin` (artwork details view) and `ArtworkOrderAdmin` (sales order details view).
- Enforce full test coverage adhering to the project's Django testing contract.

**Non-Goals:**
- Automatic monetary calculations or split payouts (administrators calculate currency splits manually as needed).
- Snapshotting historical commissions on `ArtworkOrder` (sales orders dynamically display the artist's commission rate).
- Exposing commission in public REST APIs or serializers (strictly internal admin data).

## Decisions

### 1. Model field type: PositiveSmallIntegerField with min/max validators
- **Decision**: Use `models.PositiveSmallIntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)], verbose_name="Comisión del artista (%)", help_text=...)` on `Artist`.
- **Rationale**: Represents percentages (0–100) efficiently at the database level and enforces bounds through Django's model validation.
- **Alternatives considered**:
  - `DecimalField(max_digits=5, decimal_places=2)`: Overkill and unnecessary precision since the business requirement specifies whole percentage numbers (integers 0 to 100).
  - `IntegerField`: Allows negative numbers unless explicitly validated; `PositiveSmallIntegerField` is cleaner and standard in Django.

### 2. Changelist placement and formatting in ArtistAdmin
- **Decision**: Define `@admin.display(description="Comisión", ordering="commission") def display_commission(self, obj): return f"{obj.commission}%"` and position it second in `list_display` (`["display_name", "display_commission", "display_email", ...]`).
- **Rationale**: Fulfills the requirement to be visible "next to the first columns" right alongside the artist's name, while supporting sorting by commission rate.
- **Alternatives considered**:
  - Raw `"commission"` field name in `list_display`: Would render plain numbers (`25`) without the percentage context symbol (`25%`).

### 3. Readonly display helper in ArtworkAdmin and ArtworkOrderAdmin
- **Decision**: Implement `@admin.display(description="Comisión del artista") def display_artist_commission(self, obj):` on both `ArtworkAdmin` and `ArtworkOrderAdmin`.
  - In `ArtworkAdmin`: Reads `obj.artist.commission` if `obj.artist` exists.
  - In `ArtworkOrderAdmin`: Reads `obj.artwork.artist.commission` if `obj.artwork and obj.artwork.artist` exists.
  - Both format as `f"{commission}%"` or return `"-"` when missing.
- **Rationale**: Simple, robust, zero extra database fields required on `Artwork` or `ArtworkOrder`.
- **Alternatives considered**:
  - Adding a database column on `ArtworkOrder`: Unnecessary since automatic payout computation and frozen historical commissions are explicitly out of scope.

### 4. Exclusion from public APIs
- **Decision**: Do not add `commission` to `ArtistSerializer`, `ArtworkSerializer`, or any public API view.
- **Rationale**: Commission splits are private commercial agreements between Enredarte and individual artists; leaking them via public JSON endpoints would violate privacy.

## Risks / Trade-offs

- **[Risk] Existing artist records receive default 0% commission** → Mitigation: `default=0` safely applies across existing database records without migration prompts; administrators can update existing artists' commissions in the admin as agreed.
- **[Risk] Changing an artist's commission alters the displayed rate on past sales** → Mitigation: Explicit non-goal per product requirements. The readout dynamically reflects the artist's configured commission rate.

## Migration Plan

1. Create migration `artworks/migrations/0013_artist_commission.py` via `python manage.py makemigrations artworks`.
2. Apply migration via `python manage.py migrate`.
3. Verify backward-compatibility and existing seed fixtures.
