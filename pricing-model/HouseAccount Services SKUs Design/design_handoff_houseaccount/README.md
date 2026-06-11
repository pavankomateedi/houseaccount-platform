# Handoff: HouseAccount.AI — Home Services Marketplace

## Overview
HouseAccount.AI is a services e-commerce platform for home chores and fixes. Customers browse a catalog of services (TV mounting, plumbing, painting, furniture assembly, etc.) offered by two kinds of providers — **companies** (storefront businesses with teams) and **individual pros** (independent handymen/specialists) — view rich provider profiles, open service detail pages (PDP) modeled on classic Shopify product pages, and add services to a cart that mixes **fixed-price bookings** with **free quote requests**.

This package documents every screen so a developer can implement the application in a real codebase. The list of webpages should work on desktop and be implementable as an iOS or Android app (the design is fully responsive down to ~360px).

## About the Design Files
The files bundled in `design_files/` are **design references created in HTML** — a clickable React-in-Babel prototype showing intended look and behavior. They are **not production code to copy directly**. The task is to **recreate these designs in the target codebase's existing environment** (React/Next.js, Vue, SwiftUI, Kotlin, etc.) using its established patterns, routing, and component libraries — or, if no codebase exists yet, choose an appropriate stack (e.g. Next.js + a REST/GraphQL backend) and implement the designs there.

Open `design_files/HouseAccount.html` in a browser to interact with the live prototype while reading these specs.

## Fidelity
**High-fidelity.** Colors, typography, spacing, radii, copy, and interactions are final design intent. Recreate the UI pixel-faithfully using the target codebase's libraries. The only intentionally-provisional elements are the images: illustrated placeholder art (storefronts, portraits) and drag-and-drop photo slots stand in for real photography.

## Screen Specs (one file per screen)
| File | Screen | Route in prototype |
|---|---|---|
| `screens/01-catalog.md` | Catalog / browse (services + providers tabs) | `#/catalog`, `#/catalog/providers` |
| `screens/02-company-profile.md` | Company storefront profile | `#/provider/brightfix`, `#/provider/oakline` |
| `screens/03-individual-profile.md` | Individual pro profile | `#/provider/marcus`, `#/provider/sofia` |
| `screens/04-service-detail.md` | Service detail page (PDP) | `#/service/<id>` |
| `screens/05-cart-drawer.md` | Cart drawer (bookings + quote requests) | overlay, any route |

Shared building blocks are in `components.md`; entities and seed data are in `data-model.md`.

## Global Design Tokens

### Colors
| Token | Value | Usage |
|---|---|---|
| `--primary` | `#1d4e89` | Brand blue: buttons, links, active states, logo mark, hero bg. **User-tweakable** — all derived tints use `color-mix`. Alternates explored: `#2e7d52`, `#0f766e`, `#b4540a` |
| `--ink` | `#16263a` | Primary text, dark surfaces (toast, "Popular" flag) |
| `--muted` | `#5d6b7d` | Secondary text, labels, icons |
| `--green` | `#2e7d52` | Trust/success: badges, prices ("Free quote"), availability-ok, cart count |
| `--green-soft` | `#e7f3ec` | Background for trust badges, availability-ok pill |
| `--bg` | `#f5f7fa` | Page background |
| `--card` | `#ffffff` | Card/panel surfaces |
| `--line` | `#e2e8f0` | Borders, dividers (1px solid; 1.5px on inputs/controls) |
| `--star` | `#f5a623` | Star ratings fill |
| Warn pill | bg `#fdf1e2`, text `#a05a12` | Urgency availability ("2 slots left this week") |
| Body text alt | `#3c4a5c` / `#2e3d50` | Long-form paragraph text (about, reviews, includes) |
| Scrim | `rgba(13,24,38,.42)` | Drawer overlay |

Derived tints (use `color-mix(in oklab, var(--primary) N%, white)`): nav active bg 9%, segmented active bg 10%, option-selected bg 7%, hover borders 30–50%.

### Typography
| Role | Font | Size / weight |
|---|---|---|
| Display / headings | **Plus Jakarta Sans** (Google Fonts), weights 500–800 | h1 30px/800 (hero clamp 28–40px), section h2 21px/800, card h3 16–17.5px/700, letter-spacing −0.01 to −0.025em |
| Body | **Public Sans**, weights 400–700 | base 15px, line-height 1.5; meta 12.5–13.5px |
| Prices | Plus Jakarta Sans 800 | card 17px, PDP 30px, cart total 19px |
| Overline labels | Public Sans 700 | 11.5–13px, uppercase, letter-spacing .04–.06em |

### Spacing & Layout
- Content container: `min(1180px, 100% − 48px)` centered; mobile `100% − 32px`.
- Card grid gap 18px; section vertical rhythm 36px; panel padding 20–22px.
- Header height 64px, sticky, `rgba(255,255,255,.92)` + `backdrop-filter: blur(10px)`, bottom 1px `--line`.

### Radius & Shadows
- Cards/panels: `--radius` = **14px** (user-tweakable 4–24px). Buttons 10px (lg 12px, sm 8px). Chips/badges 999px. Inputs/segments 10–12px.
- Card hover: `box-shadow: 0 10px 28px -10px rgba(22,38,58,.18)` + `translateY(-2px)` + primary-tinted border; transition 180ms.
- Drawer: `-18px 0 50px -20px rgba(13,24,38,.35)`.
- Toast: `0 12px 32px -8px rgba(13,24,38,.4)`.

### Breakpoints
| Width | Change |
|---|---|
| ≤1180px | PDP loses third column; "You may also like" becomes a horizontal wrap row spanning full width |
| ≤1020px | Profile pages & PDP collapse to single column; sticky sidebars become static (individual profile card ordered first); review grid 1-col; gallery 2-col |
| ≤760px | Header: nav links + wordmark hidden (logo mark + search + cart only); stat rows 2×2; service rows wrap; toolbar stacks; hero tightens |

## Interactions & Behavior (global)
- **Routing**: hash-based in the prototype (`#/catalog`, `#/catalog/providers`, `#/provider/:id`, `#/service/:id`). Map to real routes in production. Route change scrolls to top.
- **Cart**: persists (`localStorage` key `ha-cart-v1` in prototype → server-side cart in production). Adding any item opens the drawer and shows a toast.
- **Toast**: bottom-center, ink bg, white text, check icon, slide-up 250ms `cubic-bezier(.3,1.2,.4,1)`, auto-dismiss 2.6s.
- **Buttons**: primary = `--primary` bg, white text, hover `filter: brightness(1.12)`; ghost = white bg, 1.5px `--line` border, hover primary border+text.
- **Cards**: entire card clickable (role="link", Enter key support); inner provider link stops propagation.
- **Tweaks**: prototype exposes primary color, card radius, catalog density as live controls — these map to theme config, not user-facing features.

## State Management
- `route` — current page + params.
- `cart: CartItem[]` — `{ key, kind: 'book'|'quote', serviceId, optionIndex?, qty? }`. Booked items merge on `serviceId+optionIndex` (qty increments); quote requests dedupe per service.
- `query` — global search string (header input), filters catalog live.
- Catalog-local: `tab` (services|providers), `cat` (category id|all), `who` (all|company|individual), `price` (all|fixed|quote).
- PDP-local: `opt` (option index), `qty`, `addonOn`, `addonOpen` — all reset on service change.
- `drawerOpen`, `toast`.
- Data fetching: catalog (services+providers, filterable), provider by id (with services, reviews), service by id (with provider, related services).

## Assets
All in `design_files/houseaccount/img/` — flat illustrations generated for the prototype; replace with real photography in production:
- `brightfix-storefront.png` (1200×420) — company banner
- `oakline-storefront.png` (1200×420) — company banner
- `marcus-portrait.png` (600×600) — individual pro avatar/portrait
- `sofia-portrait.png` (600×600) — individual pro avatar/portrait

Icons are a custom 24×24 stroke set (1.8px, round caps) defined in `design_files/houseaccount/icons.jsx` — includes one icon per service category plus UI glyphs (search, cart, star, shield, clock, pin, chevrons, bolt, user, store, message, calendar, plus/minus, close, check). Empty image areas use a drag-and-drop `<image-slot>` placeholder component — in production these are upload targets / CMS images.

## Files
```
design_files/
  HouseAccount.html            — entry: all CSS tokens & styles, script loading
  houseaccount/data.js         — seed data (see data-model.md)
  houseaccount/icons.jsx       — icon set
  houseaccount/ui.jsx          — shared atoms & cards (see components.md)
  houseaccount/chrome.jsx      — header, footer, cart drawer, toast
  houseaccount/page-catalog.jsx
  houseaccount/page-provider.jsx — both profile layouts
  houseaccount/page-service.jsx  — PDP + "You may also like"
  houseaccount/app.jsx         — routing, cart state, tweaks
  houseaccount/img/            — illustrated placeholder assets
```
