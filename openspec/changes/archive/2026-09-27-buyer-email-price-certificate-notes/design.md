## Context

Buyer mails are rendered per-audience from `artworks/sale_notifications.py` via `core.mail_utils.send_audience`, with templates at `artworks/templates/artworks/email/sale_<kind>_buyer.{txt,html}`. Every buyer template carries Spanish first + English section after in the same file (TXT and HTML kept in sync). `ArtworkOrder.amount` (`artworks/models.py:295-298`) is defined as "Monto cobrado (foto del precio al momento de la compra)" — artwork price only; no delivery-cost field exists on the order. Only three buyer templates render `{{ amount }}`: reserved, paid, refunded. Certificate + secure delivery is universal for every sale (operator-confirmed), but is never stated in any buyer mail today.

## Goals / Non-Goals

**Goals:**
- Disambiguate the Stripe-charged amount (artwork-only, delivery agreed separately) wherever a buyer sees money.
- State certificate + secure delivery at the two money moments (reserved, paid) to build trust.
- Keep the established inline ES+EN pattern; zero Python / model / Stripe changes.

**Non-Goals:**
- No subject, audience, trigger, or best-effort-semantics changes.
- No `locale/` + `{% trans %}` migration; no shared `{% include %}` partial.
- No delivery-price field, no checkout-flow change; no artist/admin copy change.
- No changes to delivery_complete / shipped / delivered / cancelled buyer bodies.

## Decisions

1. **Static copy in 6 template files, no code change** — rationale: `amount` has no delivery component to compute and the notes are unconditional; adding context vars or senders would be YAGNI. Alternative (pass `price_note` via `_sale_context`) rejected: more code for zero dynamic content. Alternative (`{% include %}` partial) rejected: 1–2 sentences × 3 files does not justify indirection yet.
2. **Placement: price note directly after the `Monto:` line; certificate line directly after the `Obra:` line, as plain `<p>` like surrounding body text** (operator decision 2026-09-27: no `.muted` styling) — rationale: adjacency kills the misreading at the point of confusion; certificate reads as a property of the work, not a PS. Same order in TXT and HTML, ES and EN blocks.
3. **Vague delivery wording, no channel named** (operator decision in explore: "Keep it vague") — `El costo de envío se acuerda por separado / Delivery cost is agreed separately.` Alternative (name reply-to-email or delivery-form channel) rejected per operator input.
4. **Refunded buyer gets the price note too** — rationale: it also renders `Monto reembolsado: {{ currency }} {{ amount }}`; consistency beats brevity. No certificate line there (failed sale, promise would read wrong).
5. **Reserved uses the universal variant, paid uses the direct variant** — reserved (pre-payment) sells trust: `Todas nuestras obras incluyen… / All our artworks include…`; paid (post-payment) confirms: `Tu obra incluye… / Your artwork includes…`.

Exact copy (locked in explore):
- Price ES: `Nota: este monto corresponde únicamente al precio de la obra. El costo de envío se acuerda por separado.`
- Price EN: `Note: this amount covers the artwork price only. Delivery cost is agreed separately.`
- Cert ES (paid): `Tu obra incluye certificado de autenticidad y entrega segura coordinada por nuestro equipo.`
- Cert EN (paid): `Your artwork includes a certificate of authenticity and secure delivery coordinated by our team.`
- Cert ES (reserved): `Todas nuestras obras incluyen certificado de autenticidad y entrega segura.`
- Cert EN (reserved): `All our artworks include a certificate of authenticity and secure delivery.`

## Risks / Trade-offs

- [Risk] TXT and HTML drift (only one updated) → Mitigation: tasks require editing both alternatives per template; verification greps both.
- [Risk] Future delivery-price field makes the note stale → Mitigation: note is static and vague by design; a priced-delivery change would revisit these three templates explicitly.
- [Risk] Duplicate shell change `buyer-price-certificate-notes/` (empty, only `.openspec.yaml`, never filled) causes confusion → Mitigation: removed per operator decision (2026-09-27); only `buyer-email-price-certificate-notes` remains. No file overlap.
- [Risk] Tests asserting exact buyer bodies would break → Mitigation: verified — current `SaleEmailNotificationsTest` / `ArtworkOrderWebhookEmailTest` assert subjects/audiences/transitions, not the new sentences.
