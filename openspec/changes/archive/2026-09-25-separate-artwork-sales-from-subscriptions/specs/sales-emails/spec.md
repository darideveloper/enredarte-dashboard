## ADDED Requirements

### Requirement: Sale senders and templates owned by artworks

The system SHALL provide `artworks/sale_notifications.py` exposing `send_sale_reserved`, `send_sale_paid`, `send_sale_delivery_complete`, `send_sale_shipped`, `send_sale_delivered`, `send_sale_cancelled`, and `send_sale_refunded` with audiences, Spanish subjects, per-audience skip-and-log, and best-effort semantics identical to today. Sale templates SHALL live under `artworks/templates/artworks/email/sale_{reserved,paid,delivery_complete,shipped,delivered,cancelled,refunded}_{buyer,artist,admin}.txt|.html` (same 36 files, same bodies), and SHALL be resolved by the renderer through the `artworks/email/sale_*` namespace. `subscriptions/services/notifications.py` SHALL NOT contain sale senders, and `subscriptions/templates/subscriptions/email/sale_*` SHALL NOT exist. All sale callers (buy/summary/delivery views, `artworks/services.py` reconcile, sync/release commands, order webhook path, `ArtworkOrderAdmin` shipped/delivered/cancel actions) SHALL import from `artworks.sale_notifications`.

#### Scenario: Paid sale still mails trio from artworks module

- **WHEN** `send_sale_paid(order)` runs with buyer, artist, and two admin addresses configured
- **THEN** three messages SHALL be sent (buyer, artist, admin-list) with the same subjects and TXT+HTML bodies as today, rendered from `artworks/email/sale_paid_*` templates.

#### Scenario: Sale mail renders from artworks template namespace

- **WHEN** any `send_sale_*` sender renders its TXT and HTML bodies
- **THEN** the resolved template names SHALL begin with `artworks/email/sale_`, and no `subscriptions/email/sale_*` template SHALL be required to render.

#### Scenario: Sale mail failure keeps the state

- **WHEN** SMTP raises during a best-effort sale send
- **THEN** the already-persisted order/artwork state SHALL remain, the failure SHALL be logged, and no caller SHALL roll back or turn a webhook 200 into a 500.
