## 1. Model & Database Migration

- [x] 1.1 Add `commission` field to `Artist` in `artworks/models.py` with `PositiveSmallIntegerField`, `MinValueValidator(0)`, `MaxValueValidator(100)`, `default=0`, `verbose_name="Comisión del artista (%)"`, and descriptive Spanish `help_text`.
- [x] 1.2 Generate and run database migration (`0013_artist_commission.py`), verifying `python manage.py migrate` applies without warnings.

## 2. Django Admin Views

- [x] 2.1 Update `ArtistAdmin` in `artworks/admin.py`: implement `display_commission` formatted as `f"{obj.commission}%"`, place it after `display_name` in `list_display`, and add `commission` under a dedicated `"Acuerdo comercial"` fieldset.
- [x] 2.2 Update `ArtworkAdmin` in `artworks/admin.py`: implement `display_artist_commission`, add it to `readonly_fields`, and place it in the change form `fieldsets`.
- [x] 2.3 Update `ArtworkOrderAdmin` in `artworks/admin.py`: implement `display_artist_commission` reading `obj.artwork.artist.commission`, add it to `readonly_fields`, and place it in the `"Pedido"` fieldset.

## 3. Automated Tests & Verification

- [x] 3.1 Add unit tests in `artworks/tests.py` covering:
  - Model bounds validation (`0` allowed, `100` allowed, `-1` rejected, `101` rejected, default `0`).
  - `ArtistAdmin` changelist rendering showing commission percentage.
  - `ArtworkAdmin` change view rendering artist commission.
  - `ArtworkOrderAdmin` change view rendering artist commission from the sold artwork.
  - Asserting public artist and artwork serializers do not expose `commission`.
- [x] 3.2 Run test suite via `python manage.py test artworks` and verify testing contract guard with `bash .opencode/commands/guard.sh`.
