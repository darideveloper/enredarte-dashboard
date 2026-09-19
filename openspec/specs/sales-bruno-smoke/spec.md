# sales-bruno-smoke Specification

## Purpose
TBD - created by archiving change add-sales-bruno-docs. Update Purpose after archive.
## Requirements
### Requirement: Headless smoke run over the sales flow
The project SHALL document a headless `bru run` smoke command over the
`Sales/` folder against the dev server. The run SHALL require no
credentials. Accepted outcomes: buy → `201` or `409` (real artwork slug;
artwork state dependent), or `404` (committed example slug `obra-ejemplo`
unknown in that DB — benign, proves routing + error envelope);
order-summary → `200` or `404`; delivery is excluded from the
smoke run by design (it requires a paid order — manual only). The command
SHALL be documented in `bruno/README.md` only (no script file, no CI
wiring).

#### Scenario: Smoke run on a fresh dev DB
- **WHEN** `bru run` executes the `Sales/` folder against dev
- **THEN** the buy request SHALL return `201`, `409`, or `404` (example
  slug unknown) and the run SHALL be considered passing on those codes
  (no hard failure on `409` or `404`).

#### Scenario: No credentials needed
- **WHEN** the smoke command is executed without any environment secrets
- **THEN** it SHALL run to completion (sales endpoints are public).

