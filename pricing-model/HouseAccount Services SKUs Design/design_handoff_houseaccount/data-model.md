# Data Model & Seed Data

Source of truth in the prototype: `design_files/houseaccount/data.js`.

## Entities

### Category
11 fixed service categories, each with an id, display name, and a dedicated stroke icon + hue for thumbnail tiles.

| id | name | tile hue (oklch H) |
|---|---|---|
| `repairs` | Repairs | 214 |
| `tv-mounting` | TV Mounting | 250 |
| `plumbing` | Minor Plumbing | 199 |
| `electrical` | Minor Electrical | 42 |
| `home-mods` | Home Modifications & Upgrades | 168 |
| `carpentry` | Carpentry & Drywall | 28 |
| `doors` | Doors | 16 |
| `painting` | Painting or Staining | 330 |
| `furniture` | Furniture Assembly | 150 |
| `flooring` | Flooring & Tiling | 264 |
| `other` | Other / Multiple | 214 |

Category tile background: `linear-gradient(135deg, oklch(0.955 0.025 H), oklch(0.90 0.05 H+20))`, icon color `oklch(0.45 0.10 H)`.

### Provider
```ts
interface Provider {
  id: string;
  type: 'company' | 'individual';
  name: string;
  tagline: string;             // one-liner under name
  about: string;               // paragraph for profile page
  rating: number;              // 0–5, one decimal
  reviewCount: number;
  yearsInBusiness: number;
  jobsCompleted: number;
  responseTime: string;        // "Usually responds in ~1 hour"
  badges: BadgeId[];           // ordered, first is most prominent
  serviceArea: string;         // "Within 25 mi of downtown"
  hours: string;               // "Mon–Sat · 7am–7pm"
  guarantee: string;           // "12-month workmanship guarantee"
  // company only
  team?: number;
  storefrontImg?: string;      // banner image
  // individual only
  hourlyRate?: number;
  skills?: string[];           // chips on profile
  photo?: string;              // portrait, used as avatar everywhere
  avatarInitials: string;      // fallback avatar
  avatarHue: number;           // fallback avatar color
}
```

### BadgeId → trust badge copy
| id | label | tooltip/desc |
|---|---|---|
| `verified` | Verified Pro | Identity & credentials verified by HouseAccount |
| `licensed` | Licensed | Trade licenses on file & current |
| `insured` | Insured | Liability insurance up to $1M |
| `background` | Background-checked | Passed a third-party background check |

### Service
```ts
interface Service {
  id: string;
  providerId: string;
  category: CategoryId;
  name: string;
  blurb: string;                 // one-line pitch
  priceModel: 'fixed' | 'hourly' | 'quote';
  price?: number;                // fixed: all-in price; hourly: $/hr
  priceFrom?: number;            // quote with floor ("from $4")
  priceUnit?: string;            // e.g. "/sq ft"
  time: string;                  // estimate: "60–90 min", "Up to 2 hrs", "Quote in 24 hrs"
  rating: number;
  reviewCount: number;
  popular?: boolean;             // shows "Popular" flag on card
  includes: string[];            // 4–5 bullets, "What's included"
  options?: {                    // single-axis variant (PDP)
    label: string;               // "TV size", "Door type", "Items"
    choices: { name: string; delta: number }[];  // delta added to price
  };
  sku?: string;                  // "HA-BF-TVM01" — shown on PDP byline
  addon?: { name: string; price: number };       // warranty-style checkbox on PDP
  availability?: { text: string; tone: 'ok' | 'warn' };  // urgency line on PDP
}
```

### Review
```ts
interface Review {
  name: string;      // "Dana P."
  rating: number;    // 1–5
  date: string;      // "May 2026"
  service: string;   // service name shown next to date
  text: string;      // 1–3 sentences, concrete and specific
}
```
Keyed by provider id in the prototype; production should key by service too.

### CartItem
```ts
interface CartItem {
  key: string;                  // serviceId + '-' + optionIndex (book) | serviceId + '-q' (quote)
  kind: 'book' | 'quote';
  serviceId: string;
  optionIndex?: number;
  qty?: number;                 // min 1; for hourly services qty = hours
}
```
Subtotal = Σ over `book` items of `(price + optionDelta) × qty`. Quote items are always free.

## Seed Data Summary

### Providers (4)
| id | type | name | rating | reviews | yrs | jobs | badges |
|---|---|---|---|---|---|---|---|
| `brightfix` | company | BrightFix Home Services | 4.9 | 1,243 | 12 | 4,823 | verified, licensed, insured, background |
| `oakline` | company | Oakline Carpentry Co. | 4.8 | 587 | 9 | 1,976 | verified, licensed, insured |
| `marcus` | individual | Marcus Webb | 4.8 | 412 | 6 | 1,138 | verified, background |
| `sofia` | individual | Sofia Ramirez | 5.0 | 268 | 8 | 743 | verified, background, insured |

### Services (16)
| id | provider | category | price | model | notes |
|---|---|---|---|---|---|
| `bf-tv-mount` | brightfix | tv-mounting | $129 | fixed | options: TV size (+$0/+$40/+$90); addon surge strip $19; popular |
| `bf-plumbing` | brightfix | plumbing | $149 | fixed | addon leak sensor $15 |
| `bf-electrical` | brightfix | electrical | $159 | fixed | |
| `bf-repairs` | brightfix | repairs | $119 | fixed | popular; warn availability |
| `bf-home-mods` | brightfix | home-mods | from $95 | quote | |
| `bf-other` | brightfix | other | — | quote | "describe it" catch-all |
| `ok-doors` | oakline | doors | $189 | fixed | options: slab/prehung (+$110); addon haul-away $20 |
| `ok-drywall` | oakline | carpentry | $169 | fixed | |
| `ok-flooring` | oakline | flooring | from $4/sq ft | quote | popular |
| `ok-painting` | oakline | painting | $449 | fixed | addon ceiling $129; warn availability |
| `mw-furniture` | marcus | furniture | $69 | fixed | options: 1/2/3 items (+$49/+$89); addon anchor kit $12; popular; warn availability |
| `mw-tv-mount` | marcus | tv-mounting | $79 | fixed | addon cord cover $15 |
| `mw-hourly` | marcus | other | $55/hr | hourly | 2 hr minimum |
| `sr-accent-wall` | sofia | painting | $199 | fixed | addon touch-up kit $19; popular; warn availability |
| `sr-staining` | sofia | painting | — | quote | photo-based quotes |
| `sr-drywall` | sofia | carpentry | $139 | fixed | |

Full copy (blurbs, includes bullets, availability strings, review texts) lives in `design_files/houseaccount/data.js` — treat that copy as final content design.
