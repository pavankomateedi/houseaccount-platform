# Screen 03 — Individual Pro Profile

**Route**: `#/provider/marcus`, `#/provider/sofia` (any provider with `type: 'individual'`)
**Purpose**: A personal profile for an independent pro. Same trust-building job as the company storefront but human-first: big portrait, first-name copy, personal skills, hourly base rate. Spotlights the person the customer will actually meet.

## Differences vs. company profile (02)
| | Company | Individual |
|---|---|---|
| Top of page | Full-bleed storefront banner + overlapping logo | No banner — profile card in a left sidebar |
| Column order | Content left, trust sidebar right (330px) | **Profile sidebar left (330px), content right** |
| Identity | Logo block, "COMPANY" tag, team size | 132px circular portrait, "INDIVIDUAL PRO" tag, hourly rate |
| Stats | 4-stat band across the page | Compact 3-stat panel under the profile card |
| About heading | "About {Company Name}" | "Meet {FirstName}" + skills chips |
| Trust copy | "Why you can trust them" | Trust facts inside the profile card |
| Message CTA | Ghost "Message the team" | **Primary** "Message {FirstName}" (primary action) |

## Layout
Two-column grid `330px 1fr`, 28px gap, 36px top margin.

### Left sidebar (sticky, top 84px)
1. **Persona card** (white panel, items left-aligned, 10px gap):
   - Portrait — 132px circle, centered (illustrated default; photo drop slot).
   - "INDIVIDUAL PRO" overline (primary color).
   - Name — Jakarta 800 25px. Tagline 14px muted.
   - RatingLine (15px).
   - Compact trust badges row.
   - **Rate line**: "$55/hr" Jakarta 800 19px + muted "base rate · fixed prices below".
   - **Primary full-width** "Message {FirstName}" with message icon.
   - Facts block (dashed top border, 13px): bolt response time · pin service area · calendar hours · check guarantee ("Free return visit if anything's off").
2. **Mini-stats panel**: 3 StatBlocks spread horizontally — years experience · jobs done · avg rating.

### Right column (36px section rhythm)
1. **Meet {FirstName}** — h2 + about paragraph (first-person voice) + **skills chips** (e.g. Furniture Assembly, TV Mounting, Smart Home…).
2. **Services & pricing — the menu** — identical component to company profile: category-grouped ServiceRows with Add / Request quote buttons.
3. **Recent work** — 4-up square photo grid (drop slots).
4. **Reviews** — h2 + RatingLine + 2-col ReviewCard grid.

## Content rules
- Copy uses the pro's first name everywhere ("Message Marcus", "Drop Marcus's photo", "Meet Sofia").
- About text is first-person and personal; keep it that way in production CMS.
- Hourly rate only shows when the pro has one (`hourlyRate`); pure fixed-price pros omit the rate line.

## Interactions
Same as company profile: rows → PDP, row buttons → cart/quote, message → thread (toast in prototype).

## Responsive
- ≤1020px: single column; **persona card first** (order −1), then content; no sticky.
- ≤760px: service rows wrap their price/button to a full-width bottom row.
