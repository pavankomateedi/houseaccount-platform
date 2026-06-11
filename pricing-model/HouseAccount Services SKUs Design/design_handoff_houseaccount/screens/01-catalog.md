# Screen 01 — Catalog / Browse

**Route**: `#/catalog` (services tab) · `#/catalog/providers` (providers tab)
**Purpose**: Entry point. Customers search and filter all services and providers, compare prices/ratings at a glance, and jump into a service PDP or provider profile.

## Layout
Full-width hero band, then a 1180px container with: toolbar (tabs + filters) → category chip rail → responsive card grid. Footer below.

### Hero
- Background: `linear-gradient(160deg, color-mix(--primary 96% black), color-mix(--primary 72% #0c1a2e))`, white text, padding 46px top / 42px bottom.
- H1 "Every fix, one account." — Jakarta 800, `clamp(28px, 4vw, 40px)`, −0.025em.
- Subline (max 560px, 16px, white 85%): "Book trusted companies and independent pros for repairs, upgrades, and everything your home throws at you — upfront prices, real reviews."
- Trust strip — 3 inline items, 13.5px/600, icons at 15px: shield "Verified & background-checked pros" · check "Upfront pricing — or a free quote" · bolt "Most pros reply within an hour".

### Toolbar (margin 26px top, 14px bottom)
- **Tabs** (left): segmented control in a white 1.5px-bordered 12px-radius shell. "Services" / "Providers", each with a live count pill. Active tab: `--primary` bg, white text. 8×16px padding.
- **Filters** (right, wrap):
  - Provider type segment: `All pros | Companies | Individuals` — active = primary text on 10% primary tint.
  - Pricing segment (services tab only): `Any price | Upfront price | Quote-based`.

### Category rail
Horizontally scrollable row of pill chips (8px gap): "All" + the 11 categories, each with its 15px category icon. Default white/1.5px border; active = primary bg, white text; hover = primary-tint border. Single-select.

### Grid
- **Services tab**: `repeat(auto-fill, minmax(280px, 1fr))`, 18px gap (density tweak: 236px min). Cards per `components.md → ServiceCard`.
- **Providers tab**: `minmax(330px, 1fr)`. Cards per `components.md → ProviderCard`.
- **Empty state**: centered muted "No services match — try clearing a filter." + ghost "Clear filters" button (resets cat/who/price).

## Filtering & Search Logic
- All filters AND-combine: category, provider type, price model, search query.
- Search (header input) matches service name + blurb + category name + provider name; on providers tab: provider name + tagline + their service names. Case-insensitive substring.
- Tab counts update live with current filters.
- Provider-type filter applies on both tabs; on providers tab the category filter keeps providers offering ≥1 service in that category.

## Interactions
- Service card click → PDP. Provider row inside card → provider profile (no PDP navigation).
- Provider card click → profile.
- "Book/Get quote →" is visual affordance — whole card is the link.
- Typing in header search while on another page routes back to catalog with the query applied.

## Responsive
- Grid auto-fills (1 col ≈360px, 2 cols ≈600px, 4 cols at 1180px).
- ≤760px: toolbar stacks vertically (tabs above filters); hero padding 34/30px; category rail stays a horizontal scroller.
