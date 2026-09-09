---
created: 2026-09-09
updated: 2026-09-09
tags:
  - enredarte
  - overview
  - architecture
type: guide
status: active
---

# Enredarte Overview

Project-specific map of the Enredarte dashboard: what each app owns, which hosts serve what, and where the source of truth lives for prices, visibility, and content.

## Apps

| App | Owns | Key models |
|---|---|---|
| `core` | Publish-to-production flow, base/seed fixture loaders | (no domain models; `admin/system/publish/`) |
| `artworks` | Catalog: artists, curators, artworks, taxonomy | `Artist`, `ArtCurator`, `Artwork`, `ArtworkImage`, `Gallery`, `Location`, `Discipline`, `Technique`, `Theme`, `Format`, `Scale` (+ `*Translation` rows) |
| `blog` | Editorial posts + images | `Post`, `PostTranslation`, `BlogImage` |
| `subscriptions` | Paid membership gating via Stripe | `BillingPlan` (solo singleton), `BillingPlanPriceHistory`, `ArtistSubscription`, `StripeEvent` |

## Hosts

| Surface | URL | Serves |
|---|---|---|
| Dashboard (this repo, Coolify) | `https://dashboard.enredarte.mx` | Django admin, `/api/artworks/`, `/api/blog/`, `/subscriptions/*`, `/webhooks/stripe/` |
| Landing (separate Astro repo) | `https://enredarte.mx` | Public site; consumes the dashboard APIs at build time with a DRF Token |
| Local dev | `https://enredarte-dashboard.localhost` (via `dev.sh` + portless) | Same Django app, portless subdomain |

## Source-of-truth table

| Decision | Source of truth | Notes |
|---|---|---|
| Subscription price | `BillingPlan` row in the DB (admin: **Suscripciones → Plan de suscripción**, Monto/Moneda) | `STRIPE_PRICE_ID` env is only an initial seed for fresh DBs; no code reads it at runtime. Price is dynamic and may change; existing Stripe subscriptions keep their old price. |
| Artist visibility | `Artist.is_active`, derived by `compute_is_active()` from the subscription row | Public API filters on `is_active` only. Stripe is the lifecycle driver; webhooks mirror it. |
| Display names (es/en) | `*Translation` rows (`es` first, fallback any, then slug) | Via `TranslatableName` mixin; translation rows render as `"{parent} ({language})"`. |
| Admin language | Spanish (`LANGUAGE_CODE = "es"`, `TIME_ZONE = "America/Mexico_City"`) | See [[django-i18n-es-admin\|Spanish Django Admin]]. |
| New signups on/off | `BillingPlan.is_active_for_new_signups` | Kill-switch; blocks link generation. |

## Request flow (membership)

1. Operator creates `Artist` (email required) → clicks **Generar link de suscripción**.
2. Artist pays via Stripe Checkout → `checkout.session.completed` webhook.
3. Subscription events mirror `ArtistSubscription.status` → `compute_is_active()` flips `Artist.is_active`.
4. Landing build (`enredarte.mx`) lists only `is_active` artists via `/api/artworks/artists/`.

Full flow: [[stripe-subscriptions\|Stripe Artist Subscriptions]]. Testing: [[testing-stripe\|Testing Stripe Subscriptions]].

## Appendix: sidebar icon pipeline

Per-model sidebar icons come from `ModelAdminUnfoldBase.sidebar_icon` (default `"database"`), mapped by `utils/admin_icons.build_sidebar_icon_map()`, injected via `utils/context_processors.user_palette`, and read in `project/templates/unfold/helpers/navigation.html` through the `get_item` filter in `utils/templatetags/sidebar_extras.py`. Setting the attribute on the admin class is sufficient — no per-model wiring.

## See also

- [[enredarte-artworks-blog-api\|Enredarte Artworks & Blog API]]
- [[enredarte-deploy\|Enredarte Deploy]]
- [[enredarte-fixtures-env\|Enredarte Fixtures & Environments]]
