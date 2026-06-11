"""Build the validation UI assets into public/.

Emits the JSON the static page consumes and copies the (already tested) pure
inference modules + model.json so the browser runs the identical code path as
the endpoint. Run after make_synthetic + run_eval.

Usage: python eval/export_ui.py --data data/pricing_synthetic.csv --allow-synthetic
"""

from __future__ import annotations

import argparse
import json
import shutil
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
from pricing.evaluation import evaluate  # noqa: E402
from pricing.markets import MARKETS, market_for_zip  # noqa: E402
from pricing.metrics import mape, median_ape  # noqa: E402

PUBLIC = ROOT / "public"
LIB = ROOT / "functions" / "_lib"
COPIED_MODULES = ("calibration.js", "features.js", "predict_core.js", "clarify.js")

# Synthetic service providers per market (demo data). price_factor is applied to
# the model's midpoint, so each provider is a real "pricing option" relative to
# the estimate; eta_days is the earliest availability.
PROVIDERS: dict[str, list[dict]] = {
    "New York, NY": [
        {"name": "Empire Home Pros", "rating": 4.9, "reviews": 412, "price_factor": 1.12, "eta_days": 2},
        {"name": "Five Boroughs Services", "rating": 4.7, "reviews": 286, "price_factor": 1.00, "eta_days": 3},
        {"name": "Hudson Handywork", "rating": 4.6, "reviews": 158, "price_factor": 0.91, "eta_days": 5},
    ],
    "Dallas, TX": [
        {"name": "Lone Star Home Services", "rating": 4.8, "reviews": 503, "price_factor": 1.08, "eta_days": 1},
        {"name": "Trinity Trades", "rating": 4.7, "reviews": 221, "price_factor": 0.98, "eta_days": 2},
        {"name": "Big D Dependable", "rating": 4.5, "reviews": 97, "price_factor": 0.88, "eta_days": 4},
    ],
    "SF Bay Area, CA": [
        {"name": "Golden Gate Home Collective", "rating": 4.9, "reviews": 367, "price_factor": 1.15, "eta_days": 2},
        {"name": "Peninsula Pros", "rating": 4.8, "reviews": 244, "price_factor": 1.03, "eta_days": 3},
        {"name": "Bay Area Fixers", "rating": 4.6, "reviews": 132, "price_factor": 0.93, "eta_days": 5},
    ],
}


def _round(value: float, digits: int = 2) -> float:
    return round(float(value), digits)


def _data_summary(frame, labeled, full_model, synthetic: bool) -> dict:
    base = baseline_midpoints(labeled).to_numpy(dtype=float)
    actual = labeled["final_price"].to_numpy(dtype=float)
    counts = labeled["service_category"].value_counts()
    market_counts = labeled["zip_code"].map(market_for_zip).value_counts()
    return {
        "synthetic": synthetic,
        "model_version": full_model.model_version,
        "rows": int(len(frame)),
        "priced": int(len(labeled)),
        "unique_zips": int(frame["zip_code"].nunique()),
        "markets": [
            {"name": str(name), "count": int(n)}
            for name, n in market_counts.items()
            if name is not None
        ],
        "categories": [{"name": name, "count": int(n)} for name, n in counts.items()],
        "midpoint_p50": _round(np.percentile(base, 50), 0),
        "midpoint_p90": _round(np.percentile(base, 90), 0),
        "midpoint_p95": _round(np.percentile(base, 95), 0),
        "baseline_blended_mape": _round(mape(base, actual) * 100),
        "baseline_median_ape": _round(median_ape(base, actual) * 100),
        "median_interval": _round(full_model.median_predicted_interval, 0),
    }


def _eval_report(results) -> list[dict]:
    return [
        {
            "label": r.label,
            "n": r.n,
            "baseline_mape": _round(r.baseline_mape * 100),
            "model_mape": _round(r.model_mape * 100),
            "beats": bool(r.beats_baseline),
        }
        for r in results
    ]


def _sample_rows(labeled, full_model, limit: int = 12) -> list[dict]:
    sample = labeled.head(limit).reset_index(drop=True)
    predictions = full_model.predict_frame(sample)
    rows = []
    for i in range(len(sample)):
        rows.append(
            {
                "job_id": str(sample.loc[i, "job_id"])[:10],
                "category": sample.loc[i, "service_category"],
                "zip": str(sample.loc[i, "zip_code"]),
                "market": market_for_zip(sample.loc[i, "zip_code"]) or "—",
                "description": sample.loc[i, "job_description"],
                "original_estimate": _round(sample.loc[i, "original_estimate"], 0),
                "final_price": _round(sample.loc[i, "final_price"], 0),
                "model_midpoint": _round(predictions.loc[i, "estimate_midpoint"], 0),
                "confidence": _round(predictions.loc[i, "confidence"]),
            }
        )
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=ROOT / "data" / "pricing_synthetic.csv")
    parser.add_argument("--allow-synthetic", action="store_true")
    args = parser.parse_args(argv)

    frame = load_pricing_csv(args.data)
    synthetic = guard_dataset(frame, allow_synthetic=args.allow_synthetic)
    labeled = priced(frame)

    version = "pavan-v1.0.0" + ("-synthetic" if synthetic else "")
    results, full_model = evaluate(
        frame, version=version, seed=42, test_frac=0.2, real_threshold=0.25
    )

    PUBLIC.mkdir(exist_ok=True)
    (PUBLIC / "data_summary.json").write_text(
        json.dumps(_data_summary(frame, labeled, full_model, synthetic), indent=2)
    )
    (PUBLIC / "eval_report.json").write_text(json.dumps(_eval_report(results), indent=2))
    (PUBLIC / "sample_rows.json").write_text(
        json.dumps(_sample_rows(labeled, full_model), indent=2)
    )
    (PUBLIC / "markets.json").write_text(
        json.dumps([{"name": m.name, "zips": list(m.zips)} for m in MARKETS], indent=2)
    )
    (PUBLIC / "providers.json").write_text(json.dumps(PROVIDERS, indent=2))

    for module in COPIED_MODULES:
        shutil.copy(LIB / module, PUBLIC / module)
    shutil.copy(ROOT / "functions" / "model.json", PUBLIC / "model.json")

    print(f"UI assets written to {PUBLIC.relative_to(ROOT)}/ (synthetic={synthetic})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
