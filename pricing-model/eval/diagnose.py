"""Data diagnostics — run this first on the real dataset.

Prints the distributions that drive modeling and calibration decisions:
- priced coverage and category mix,
- estimate-midpoint percentiles (sanity-check the $5k OOD cutoff = ~95th pct),
- median estimate interval (the basis for the 3x-interval OOD rule),
- baseline per-row APE distribution (reveals the real-vs-augmented split that
  separates the blended ~11.6% baseline from the real-only ~40% baseline).

Usage: python eval/diagnose.py  [--data data/pricing_real.csv]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402

from pricing.data import (  # noqa: E402
    baseline_midpoints,
    guard_dataset,
    load_pricing_csv,
    priced,
)
from pricing.metrics import mape, median_ape  # noqa: E402

DEFAULT_DATA = ROOT / "data" / "pricing_real.csv"


def _percentiles(values: np.ndarray, points: tuple[int, ...]) -> str:
    return "  ".join(f"p{p}={np.percentile(values, p):,.0f}" for p in points)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--allow-synthetic", action="store_true")
    args = parser.parse_args(argv)

    frame = load_pricing_csv(args.data)
    if guard_dataset(frame, allow_synthetic=args.allow_synthetic):
        print("=" * 60)
        print("  !! SYNTHETIC DATA - these numbers are NOT a real result")
        print("=" * 60)
    labeled = priced(frame)

    print(f"rows total:        {len(frame)}")
    print(f"rows priced:       {len(labeled)}")
    print(f"unique categories: {frame['service_category'].nunique()}")
    print(f"unique zips:       {frame['zip_code'].nunique()}")
    print()

    print("category counts (priced):")
    for category, count in labeled["service_category"].value_counts().items():
        print(f"  {category:<20} {count}")
    print()

    base = baseline_midpoints(labeled).to_numpy(dtype=float)
    actual = labeled["final_price"].to_numpy(dtype=float)

    print("estimate midpoint (priced):")
    print("  " + _percentiles(base, (50, 75, 90, 95, 99)))
    interval = (
        labeled["estimate_hi"].to_numpy(dtype=float)
        - labeled["estimate_lo"].to_numpy(dtype=float)
    )
    print(f"  median interval (hi-lo): {np.median(interval):,.0f}")
    print()

    per_row_ape = np.abs(base - actual) / actual
    print("baseline absolute percentage error (priced):")
    print("  " + _percentiles(per_row_ape * 100, (25, 50, 75, 90, 95)) + "  (%)")
    print(f"  blended MAPE:    {mape(base, actual) * 100:.2f}%")
    print(f"  blended median:  {median_ape(base, actual) * 100:.2f}%")
    for threshold in (0.25, 0.40):
        share = float((per_row_ape >= threshold).mean())
        print(f"  share with APE >= {threshold:.0%}: {share:.1%}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
