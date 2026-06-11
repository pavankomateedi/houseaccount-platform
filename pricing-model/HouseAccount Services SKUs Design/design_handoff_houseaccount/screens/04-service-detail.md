# Screen 04 — Service Detail Page (PDP)

**Route**: `#/service/<serviceId>` (e.g. `#/service/bf-tv-mount`)
**Purpose**: The product page for one service — classic Shopify-style PDP adapted to services. Customer reviews what's included, picks a variant, adds an optional extra, sees availability urgency, and either adds to cart (fixed/hourly) or requests a free quote (quote-based). A recommendations rail cross-sells related services.

## Layout
Breadcrumb ("← All services", muted, hover primary) then a **three-column grid** `1fr 1fr 232px`, 30px gap:

### Column 1 — Media & includes
1. **Main shot** — 4:3, 16px radius. Category gradient tile behind a full-size photo drop slot (default: category icon art; real job photos in production).
2. **Thumb row** — 3 small 4:3 drop slots (10px gap, 10px radius) for additional photos.
3. **What's included** — h2 18px/800 + checklist: green check icon + 14.5px `#2e3d50` text, 9px gap. 4–5 bullets from `service.includes`.

### Column 2 — Buy column (14px gap)
1. **Byline** — 13px muted: `By {Provider link} ✓ / Service#: {SKU}`. Provider name is a primary link to the profile; green shield if verified; SKU in ink 600.
2. **Title** — Jakarta 800, `clamp(22px, 2.6vw, 30px)`.
3. **Meta line** — RatingLine (15px) · clock + time estimate.
4. **Blurb** — 15px muted.
5. **Provider card** (panel, clickable → profile):
   - Label, 11px/700 uppercase: company → "SOLD & SERVICED BY" (muted); individual → "YOUR PRO — DOES EVERY JOB PERSONALLY" (primary).
   - 44px avatar (portrait img for individuals) + name + chevron; muted line — company: "Team of 14 · 12 yrs · 4,823 jobs · 12-month workmanship guarantee"; individual: "6 yrs experience · 1,138 jobs · …".
   - Green bolt response time. Right edge: 2 compact trust badges stacked.
6. **Order box** (panel, 22px padding, 16px gap):
   - **Price line**: PriceTag big (30px; reflects selected option) + muted suffix — fixed: "upfront, all-in price"; hourly: time note; quote: "free, no-obligation quote".
   - **Installments** (fixed ≥ $100 only, dashed top border): "Pay in 4 interest-free installments of **$X**" + `HA Pay` badge (primary bg, white 10.5px/800, 5px radius) + "Learn more" link. X = ceil(total/4), updates with option/qty/addon.
   - **Options** (when `service.options`): overline label ("TV SIZE" / "DOOR TYPE" / "ITEMS"), pill buttons 1.5px border 10px radius; delta shown as `+$40` small; selected = primary border + 7% primary tint.
   - **Add-on** (when `service.addon`, not quote): warranty-style row in a 1.5px-bordered 11px-radius box — checkbox (17px, accent `--primary`) + "Add {name}" 13.5px/600 + "Show details" toggle link + price right-aligned Jakarta 800. Details (when open): 12.5px muted "Added to the same visit by the same pro — no extra trip fee…". Checked → price colored primary and added to CTA total.
   - **Quantity / Hours** stepper (not quote): − / count / + in a bordered pill; label "QUANTITY" or "HOURS" (hourly services book hours, min varies by `time` copy).
   - **CTA** — full-width primary lg: `Add to cart — $258` (live total = (price+optionDelta)×qty + addon) or `Request free quote`.
   - **Availability line** under CTA: pill — ok tone: `--green-soft`/`--green` with calendar icon ("Next opening: tomorrow, 9am"); warn tone: `#fdf1e2`/`#a05a12` with bolt icon ("Marcus has 2 slots left this week").
   - **Assurance row** — 12.5px muted, green icons: first badge label + provider guarantee.
7. **Recent reviews** — h2 18px with "see all 1,243" link → profile; 2 ReviewCards.

### Column 3 — "You may also like" rail
- Heading: 13px/800 uppercase muted.
- Up to 4 **mini-cards** (vertical stack, 10px gap): 62px CatTile + name (13px/700, 2 lines) + provider name (11.5px muted) + row of star/rating · PriceTag (13.5px). Click → that service's PDP.
- Pick order: same category from other providers → popular from other providers → same provider. No duplicates, exclude current.

### Below the grid — "More from {Provider}"
h2 21px/800 + stacked ServiceRows of the provider's other services (Add / Request quote inline).

## State & behavior
- `opt`, `qty`, `addonOn`, `addonOpen` reset when navigating between services (including via rail).
- Add to cart: merges by service+option, qty accumulates; quote services dedupe (one open request per service). Both open the cart drawer + toast.
- All prices recompute live; installment line follows the full current total.

## Responsive
- ≤1180px: rail drops below as a full-width wrap row (mini-cards ~240px each); grid becomes 2-col.
- ≤1020px: single column — media, then buy column, then rail, then "More from".
