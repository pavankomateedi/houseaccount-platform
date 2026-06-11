# Screen 02 — Company Storefront Profile

**Route**: `#/provider/brightfix`, `#/provider/oakline` (any provider with `type: 'company'`)
**Purpose**: A company's storefront on the platform — establishes trust (badges, stats, guarantee), presents the full service menu grouped by category, shows past work and reviews, and lets the customer book or request quotes directly from the list.

This layout is intentionally different from the individual-pro profile (`03`): companies get a wide storefront banner + overlapping logo block + 4-stat band; individuals get a personal portrait card. Shared sections (service menu, gallery, reviews) are identical components.

## Layout (top to bottom)
1. **Banner** — full-bleed, 240px tall, the storefront image (illustrated placeholder; drag-drop photo slot). Fallback bg `linear-gradient(135deg, #dfe7f0, #cdd9e6)`.
2. **Identity row** (container; pulled up −34px over the banner):
   - **Logo block**: 92px Avatar in a white 24px-radius frame, 6px padding, shadow `0 8px 24px -8px rgba(22,38,58,.25)`.
   - **Who column** (flex-1, 40px top padding): "COMPANY" overline → name (Jakarta 800 30px) → tagline (15.5px muted) → meta line (RatingLine 15px · pin + service area) → full-size trust badges row.
   - **CTA column** (top padding 44px): primary "See services" (smooth-scrolls to the menu) + ghost "Message" (opens message thread; prototype shows toast).
3. **Stat band** — white panel, 4 equal columns (18×24px padding): years in business · jobs completed · rating + review count · team members. Numbers Jakarta 800 22px, labels 12.5px muted.
4. **Two-column body** (`1fr 330px`, 28px gap, 30px top margin):
   - **Main column** (36px section rhythm):
     - **About** — h2 "About {name}" + paragraph (max 64ch, `#3c4a5c`).
     - **Services & pricing** — h2 with muted suffix "— the menu". Services grouped by category: group header = 13px/700 uppercase muted with category icon, then ServiceRows (see `components.md`). Each row: Add → cart (fixed) or Request quote → cart as free quote item.
     - **Recent work** — h2 + 4-up square photo grid (12px gap, 12px radius). Photo drop slots in prototype; real project photos in production.
     - **Reviews** — h2 + provider RatingLine, then 2-col grid of ReviewCards (14px gap).
   - **Sidebar** (sticky, top 84px): **Trust card** panel:
     - h3 "Why you can trust them" (16px/800)
     - Badge list — one row per badge: green shield icon + bold label (13.5px) + desc (12.5px muted); plus a guarantee row (check icon, "Backed by HouseAccount if anything goes wrong").
     - Facts block (dashed top border): bolt response time · pin service area · calendar hours · user "Team of N". Icons primary, 13px muted text.
     - Ghost full-width "Message the team" button.

## Interactions
- ServiceRow click → PDP; its button adds to cart/quote without navigating (toast + drawer opens).
- "See services" scrolls to menu (offset for 80px sticky header).
- Message buttons → messaging thread (out of scope; prototype toasts "Message thread opened").

## Responsive
- ≤1020px: body collapses to one column, sidebar (trust card) follows main content, no sticky.
- ≤760px: stat band 2×2 (16px gap); CTA buttons full-width 50/50 under identity; banner stays 240px.
