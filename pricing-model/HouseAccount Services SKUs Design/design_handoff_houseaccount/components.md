# Shared Components

Source: `design_files/houseaccount/ui.jsx`, `icons.jsx`, `chrome.jsx`.

## Header (sticky, all screens)
- 64px tall, sticky top, white at 92% opacity with 10px backdrop blur, 1px bottom border `--line`. Content inside the 1180px container, flex, 22px gap.
- **Logo**: 36×36 rounded-square (10px) `--primary` mark containing a white 2.2px-stroke house glyph; wordmark "HouseAccount.AI" — Plus Jakarta Sans 800 18px, `.AI` colored `--primary`. Clicking goes home (catalog).
- **Nav links**: "Services", "Providers" — 600 weight, muted; active = primary text on 9% primary tint, 9px radius.
- **Search**: flex-1 up to 420px, right-aligned; `--bg` fill, 1.5px `--line` border, 11px radius, search icon + placeholder "Search services or pros…". Focus: primary border, white bg. Typing routes to catalog and filters live.
- **Cart button**: 42×42, 11px radius, 1.5px border, cart icon; count badge — green pill, white 11px/700 text, 2px white ring, overlapping top-right.
- ≤760px: hide nav links and wordmark; search stretches.

## Footer
White bg, top border. One row: "HouseAccount.AI — every fix, one account." + muted "Concept prototype · all providers & reviews are illustrative". 13px.

## Atoms
- **Stars**: five 24×24 star glyphs scaled to 12–16px, `#f5a623` fill with fractional fill via gradient stop (e.g. 4.8 = 4 full + 80% star); empty portion `#dde3ea`.
- **RatingLine**: stars + bold rating ("4.9") + muted count "(1,243)". 13.5px.
- **TrustBadge**: pill, `--green-soft` bg, `--green` text, shield icon, 12.5px/600 (compact: 11.5px). Tooltip = badge description.
- **Avatar**: individuals with photos → round `<img>` (object-fit cover). Fallback: tinted square (companies, 26% radius, store icon) or circle (individuals, initials), bg `oklch(0.93 0.04 H)`, fg `oklch(0.42 0.09 H)`.
- **ProviderKind**: overline tag — "COMPANY" (amber `#8a5a18`, store icon) or "INDIVIDUAL PRO" (primary, user icon), 11.5px/700 uppercase.
- **PriceTag**: Jakarta 800. Fixed `$129`; hourly `$55/hr` (unit small+muted); quote-with-floor `from $4/sq ft`; pure quote → green "Free quote" 700.
- **CatTile**: category thumbnail — gradient tile (see data-model hues) with centered category stroke icon. Used at 48–62px (rows, cart, mini-cards) and full-bleed 16:9 (cards) / 4:3 (PDP).
- **Chip**: `--bg` fill, 1px border, 999px radius, 12.5px.
- **StatBlock**: big number (Jakarta 800 22px) over 12.5px muted label.

## ServiceCard (catalog grid)
- Card: white, 1px border, `--radius`, hidden overflow. Hover: lift −2px + shadow + primary-tint border (180ms). Whole card → PDP.
- **Thumb**: 16:9 CatTile. Overlays: "Popular" flag top-left (ink pill, white 11px/700); time pill bottom-right (white 92% pill, clock icon, 11.5px).
- **Body** (14–16px padding, 7px gap): category overline → name (16px/700) → RatingLine → provider row (24px avatar + name 13px/600 + green shield if verified; hover bg `--bg`; click → profile, stops propagation) → dashed-top footer: PriceTag left, primary CTA text right ("Book →" / "Get quote →").

## ProviderCard (catalog providers tab)
20px padding. Header: 56px avatar + kind tag, name (17.5px/700), RatingLine. Then tagline (13.5px muted), up to 4 category chips (+N overflow), stats row (`12 yrs · 4,823 jobs · ⚡ Replies ~1 hour` — bolt+green for response), compact badges, dashed-top footer: "N services" muted + "View profile →" primary.

## ServiceRow (profile pages, "More from" lists)
Horizontal: 56px CatTile (12px radius) | middle: name 15.5px/700, blurb 13px muted, meta line (rating · clock time) | right column: PriceTag + button — primary "Add" (fixed/hourly) or ghost "Request quote". Row click → PDP; button click adds to cart without navigating. ≤760px the right column wraps to a full-width row.

## ReviewCard
White panel: 34px initial-circle avatar, bold name, stars + muted "May 2026 · TV Mounting", then 13.5px `#3c4a5c` body text.

## CartDrawer — see `screens/05-cart-drawer.md`

## Toast
Fixed bottom-center: ink bg, white 14px/600, green check icon, 12px radius. Messages: "Added to cart", "Quote request added — it's free", "Message thread opened (prototype)".

## image-slot (photo placeholder)
Dashed drop target where real photography belongs (banners, portraits, galleries, PDP shots). Has author-set default art where available (`src`). In production replace with real image fields + upload flows.
