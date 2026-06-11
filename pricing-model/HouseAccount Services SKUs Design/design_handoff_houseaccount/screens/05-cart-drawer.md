# Screen 05 — Cart Drawer

**Trigger**: cart button in header, or automatically on any add-to-cart / quote request.
**Purpose**: Review the order before scheduling. Uniquely mixes two item kinds: **booked services** (priced, quantity-adjustable) and **quote requests** (always free). The customer pays nothing at this stage — checkout leads to scheduling.

## Layout
Right-side overlay drawer:
- **Scrim**: full-viewport `rgba(13,24,38,.42)`, fades 220ms; click closes.
- **Panel**: `min(430px, 94vw)` wide, full height, white, shadow `-18px 0 50px -20px rgba(13,24,38,.35)`. Slides in from right, 260ms `cubic-bezier(.3,.9,.3,1)`.

### Structure (column)
1. **Header** — "Your cart" (Jakarta 800 18px) + close icon button. 18×22px padding, bottom border.
2. **Scrollable body** (14×22px padding):
   - **"BOOKED SERVICES"** section label — 12px/700 uppercase muted.
   - Line items (12px vertical padding, bottom border):
     - 48px CatTile (10px radius)
     - Middle: service name 14px/600 → option line if any ("TV size: 56–75\"", 12.5px muted) → provider name (12.5px muted) → **qty stepper** (compact − / n / + pill).
     - Right: line total Jakarta 800 15.5px (hourly shows `/hr` small) + "Remove" link (12px underlined muted, hover red `#c0392b`).
   - **"QUOTE REQUESTS"** section label + green `Free` pill (`--green-soft` bg).
   - Quote lines: tile + name + muted "{Provider} · replies with a price in ~24h"; right side green "Quote" + Remove.
   - **Empty state** (no items): centered cart icon 36px, "Nothing here yet.", ghost "Browse services" → catalog.
3. **Footer** (top border, 16×22px padding):
   - **Subtotal row** — "Subtotal" + Jakarta 800 19px amount (booked items only: Σ (price+optionDelta)×qty). If only quotes: "N quote requests — Free".
   - **Primary lg full-width CTA** — "Continue to scheduling" (any booked items) or "Send quote requests" (quotes only). *Prototype ends here; production continues to scheduling/checkout flow.*
   - Fine print, 12px muted centered: "Pay nothing until the job is scheduled. Quotes are always free."

## Behavior
- Qty stepper min 1 (use Remove to delete). Totals update live.
- Booked items keyed by service+option — same service with different options = separate lines.
- One quote request max per service; re-requesting is a no-op.
- Cart persists across sessions (`localStorage` in prototype → user cart in production).
- Drawer opens automatically on add (with toast); Escape/scrim/close dismiss it.

## Production notes
- The scheduling flow after "Continue to scheduling" (date/time selection per provider, address, payment) is **not designed yet** — next phase.
- Quote requests should create provider-side leads with a 24h SLA surfaced to the customer ("replies with a price in ~24h" is a product promise, not filler copy).
