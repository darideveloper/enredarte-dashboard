# bruno-api-collection Delta Spec

## ADDED Requirements

### Requirement: Sales flow folder with public requests
The collection SHALL contain a `Sales/` folder with three requests in run
order: `POST buy.bru` (seq 23), `GET order-summary.bru` (seq 24),
`POST order-delivery.bru` (seq 25). Sales requests SHALL reference only
`{{base_url}}` and SHALL carry no `Authorization` header (public endpoints).
`POST buy.bru` SHALL use an example artwork slug (`obra-ejemplo`);
order-summary and order-delivery SHALL use fake-hex placeholder order slugs. POST requests SHALL use the
two-block shape (`post { body: json }` + `body:json`) with example
payloads matching `artworks/serializers.py`. Each file SHALL contain a
`docs` block per the `bruno-request-docs` convention, stating "public,
throttled" with the applicable rates (`artwork_buys 20/hour`,
`artwork_orders 60/hour`).

#### Scenario: Sales folder exists with three requests
- **WHEN** the collection is opened in Bruno
- **THEN** a `Sales/` folder SHALL list `POST buy`, `GET order-summary`,
  and `POST order-delivery` in that order.

#### Scenario: No auth header on sales requests
- **WHEN** any `Sales/` request file is inspected
- **THEN** it SHALL NOT contain an `Authorization` header, and its `docs`
  block SHALL state the endpoint is public and throttled.

#### Scenario: No hardcoded hosts or real slugs
- **WHEN** any `Sales/` request file is inspected
- **THEN** its URL SHALL reference `{{base_url}}`; buy SHALL use the
  example artwork slug (`obra-ejemplo`), order requests SHALL use
  obviously-fake hex literals, with the `docs` block explaining how to
  obtain a real slug (Stripe success redirect `?order=`).
