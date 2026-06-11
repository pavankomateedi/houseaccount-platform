"""Generate REALISTIC SYNTHETIC pricing data — for development only.

This is NOT real data. Every row is fabricated. The eval harness flags this
dataset as synthetic (job_ids are not SHA-256) and refuses to report results as
real unless run with --allow-synthetic, which stamps all output SYNTHETIC. To
get real numbers, drop the provided export at data/pricing_real.csv and rerun
the same commands without that flag.

Design goal: reproduce the *structure* the brief describes so the modeling
exercise is meaningful rather than trivial:
- 18 categories, ~1432 rows, 411 priced (the supervised subset)
- the baseline (original_estimate) is right on a typical job but IGNORES scope,
  so it is accurate on most rows and wrong on a tail of unusual-scope jobs
  (mirrors the brief's ~11.6% blended / ~40% real-only baseline)
- the scope correction is a clean function of signals the model extracts (raw
  quantity via log_max_number, and the materials flag), tied to category so it
  is fully recoverable. A good model beats the scope-blind baseline modestly.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import math
import sys
from pathlib import Path
from random import Random

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pricing.markets import sample_zip, weighted_market  # noqa: E402

# Typical job price per category (USD).
CATEGORY_BASE: dict[str, float] = {
    "Plumbing": 350, "Electrical": 450, "HVAC": 900, "Cleaning": 220,
    "Pest Control": 600, "Landscaping": 550, "Handyman": 180, "Exterior": 700,
    "Appliance Repair": 280, "Auto": 500, "Chimney": 600, "Flooring": 1600,
    "General Contractor": 4000, "Moving": 1200, "Painting": 1400, "Pool": 4500,
    "Remodeling": 6500, "Roofing": 5000,
}
PRODUCTION = {
    "Plumbing", "Electrical", "HVAC", "Cleaning",
    "Pest Control", "Landscaping", "Handyman", "Exterior",
}

# Sampling weight per category. Quick chores (handyman, cleaning, small repairs)
# dominate the marketplace; major-appliance / big-ticket jobs are comparatively
# rare. Reflecting that here makes the dataset look like real booking volume.
CATEGORY_WEIGHT: dict[str, int] = {
    "Handyman": 7, "Cleaning": 6, "Plumbing": 5, "Electrical": 4,
    "Pest Control": 4, "Landscaping": 4, "Painting": 3, "Appliance Repair": 3,
    "Exterior": 3, "Moving": 2, "Flooring": 2, "Auto": 2, "HVAC": 2,
    "Chimney": 1, "Roofing": 1, "Pool": 1, "Remodeling": 1, "General Contractor": 1,
}

# (description template, typical quantity) per category. Quick chores read like
# small tasks; big-ticket jobs read like projects. The quantity {n} is the scope
# signal the model recovers via log_max_number; the category one-hot supplies the
# per-template baseline.
CATEGORY_TEMPLATE: dict[str, tuple[str, int]] = {
    "Handyman": ("Handyman visit: {n} small tasks (mount TV, hang shelves, patch drywall)", 3),
    "Cleaning": ("Standard home cleaning, {n} rooms", 4),
    "Plumbing": ("Replace {n} plumbing fixtures", 3),
    "Electrical": ("Install {n} outlets or switches", 4),
    "Pest Control": ("Pest treatment for a {n}BR home", 3),
    "Landscaping": ("Mow and trim {n} yard sections", 4),
    "Painting": ("Paint {n} rooms", 2),
    "Appliance Repair": ("Repair {n} household appliance(s)", 1),
    "Exterior": ("Power wash {n} exterior surfaces", 3),
    "Moving": ("Move {n} rooms of furniture", 4),
    "Flooring": ("Install flooring, {n} sqft", 400),
    "Auto": ("Mobile service for {n} vehicle(s)", 1),
    "HVAC": ("Service {n} HVAC unit(s)", 2),
    "Chimney": ("Inspect and sweep {n} chimney(s)", 1),
    "Roofing": ("Roof repair, {n} sections", 3),
    "Pool": ("Pool service package, {n} visits", 4),
    "Remodeling": ("Remodel {n} rooms", 2),
    "General Contractor": ("General contracting, {n} work items", 5),
}

MATERIALS_PHRASE = ", you supply materials"
DEADLINES = ["As soon as possible", "Within 1-2 weeks", "Within 1 month", "I'm flexible"]

# Scope correction the baseline misses. Small for typical jobs, large in the
# tail; coefficients < 1 keep it recoverable from the model's features.
# Irreducible noise (_PRICE_NOISE) sets the floor neither baseline nor model can
# beat, keeping the demo honest: the model wins by recovering scope, not magic.
_SCOPE_COEF = 0.22
_MATERIALS_COEF = -0.15
_QUANTITY_SIGMA = 0.6
_PRICE_NOISE = 0.11


def _synthetic_id(rng: Random) -> str:
    # Deliberately NOT a SHA-256 hash so the dataset guard flags it as synthetic.
    digest = hashlib.sha256(str(rng.random()).encode()).hexdigest()[:24]
    return f"synthetic-{digest}"


def _weighted_category(rng: Random) -> str:
    categories = list(CATEGORY_BASE)
    weights = [CATEGORY_WEIGHT[c] for c in categories]
    return rng.choices(categories, weights=weights, k=1)[0]


def _build_description(category: str, rng: Random) -> tuple[str, float, bool]:
    template, typical = CATEGORY_TEMPLATE[category]
    # scope_log ~ N(0, sigma): most jobs near typical, a tail far from it.
    scope_log = rng.gauss(0.0, _QUANTITY_SIGMA)
    quantity = max(1, round(typical * math.exp(scope_log)))
    materials = rng.random() < 0.25
    text = template.format(n=quantity) + (MATERIALS_PHRASE if materials else "")
    return text, scope_log, materials


def _generate_row(index: int, priced_indices: set[int], rng: Random) -> dict:
    category = _weighted_category(rng)
    base = CATEGORY_BASE[category]
    market = weighted_market(rng)
    zip_code = sample_zip(market, rng)
    # Market cost index (SF Bay/NYC pricier than Dallas) + within-market spread.
    cost = market.cost_index * (1.0 + 0.05 * rng.uniform(-1, 1))
    season = 1.0 + 0.05 * rng.uniform(-1, 1)
    description, scope_log, materials = _build_description(category, rng)

    # Baseline estimate ignores scope: category + market + small noise only.
    estimate = base * cost * season * (1.0 + 0.04 * rng.uniform(-1, 1))
    estimate_lo = round(estimate * 0.75, 2)
    estimate_hi = round(estimate * 1.45, 2)

    # True price applies the recoverable scope correction the baseline missed.
    correction = math.exp(_SCOPE_COEF * scope_log + (_MATERIALS_COEF if materials else 0.0))
    true_price = estimate * correction

    final_price = ""
    if index in priced_indices:
        final_price = round(true_price * math.exp(_PRICE_NOISE * rng.gauss(0, 1)), 2)

    return {
        "job_id": _synthetic_id(rng),
        "service_category": category,
        "service_subtype": "",
        "zip_code": zip_code,
        "booking_month": f"2026-{rng.randint(1, 6):02d}",
        "job_description": description,
        "estimate_lo": estimate_lo,
        "estimate_hi": estimate_hi,
        "original_estimate": round(estimate, 2),
        "final_price": final_price,
        "deadline": rng.choice(DEADLINES),
    }


def generate(rows: int, priced: int, seed: int) -> list[dict]:
    rng = Random(seed)
    indices = list(range(rows))
    priced_indices = set(rng.sample(indices, k=min(priced, rows)))
    return [_generate_row(i, priced_indices, rng) for i in indices]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rows", type=int, default=1432)
    parser.add_argument("--priced", type=int, default=411)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument(
        "--out", type=Path, default=Path(__file__).parent / "pricing_synthetic.csv"
    )
    args = parser.parse_args(argv)

    data = generate(args.rows, args.priced, args.seed)
    headers = list(data[0].keys())
    with args.out.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        writer.writerows(data)

    n_priced = sum(1 for row in data if row["final_price"] != "")
    print(f"SYNTHETIC data written: {args.out}")
    print(f"  rows: {len(data)}  priced: {n_priced}")
    print("  NOTE: fabricated data. Run the harness with --allow-synthetic.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
