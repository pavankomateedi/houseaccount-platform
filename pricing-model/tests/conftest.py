"""Shared test fixtures: synthetic/real-shaped CSVs and golden cases."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
GOLDENSET_DIR = ROOT / "eval" / "goldenset"

_CSV_HEADERS = [
    "job_id", "service_category", "service_subtype", "zip_code",
    "booking_month", "job_description", "estimate_lo", "estimate_hi",
    "original_estimate", "final_price", "deadline",
]


def _sha256_id(seed: int) -> str:
    return hashlib.sha256(str(seed).encode()).hexdigest()


def _write_csv(path: Path, rows: list[dict[str, object]]) -> Path:
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=_CSV_HEADERS)
        writer.writeheader()
        writer.writerows(rows)
    return path


@pytest.fixture
def real_csv(tmp_path: Path) -> Path:
    """20 rows with SHA-256 ids and mixed-casing categories; even rows priced."""
    categories = ["plumbing", "Pest-Control", "hvac", "Roofing", "Cleaning"]
    rows: list[dict[str, object]] = []
    for i in range(20):
        rows.append(
            {
                "job_id": _sha256_id(i),
                "service_category": categories[i % len(categories)],
                "service_subtype": "",
                "zip_code": f"{10000 + i:05d}",
                "booking_month": "2026-03",
                "job_description": f"sample job number {i}",
                "estimate_lo": 100 + i,
                "estimate_hi": 400 + i,
                "original_estimate": 250 + i,
                "final_price": 200 + i * 10 if i % 2 == 0 else "",
                "deadline": "I'm flexible",
            }
        )
    return _write_csv(tmp_path / "real.csv", rows)


@pytest.fixture
def synthetic_csv(tmp_path: Path) -> Path:
    """Rows with generated job_000xxx ids — the shape the guard must reject."""
    rows = [
        {
            "job_id": f"job_{i:06d}",
            "service_category": "Plumbing",
            "service_subtype": "",
            "zip_code": f"{20000 + i:05d}",
            "booking_month": "2026-01",
            "job_description": "synthetic job",
            "estimate_lo": 100,
            "estimate_hi": 200,
            "original_estimate": 150,
            "final_price": 160,
            "deadline": "I'm flexible",
        }
        for i in range(10)
    ]
    return _write_csv(tmp_path / "synthetic.csv", rows)


@pytest.fixture
def calibration_cases() -> dict:
    return json.loads((GOLDENSET_DIR / "calibration_cases.json").read_text())


@pytest.fixture
def trainable_frame():
    """90 deterministic priced rows where final_price tracks the estimate.

    Big enough to fit the quantile model and assert sane behavior without the
    real dataset; not a substitute for it.
    """
    import pandas as pd

    categories = ["Plumbing", "HVAC", "Electrical", "Cleaning", "Pest Control", "Roofing"]
    bases = {"Plumbing": 400, "HVAC": 900, "Electrical": 500, "Cleaning": 250,
             "Pest Control": 700, "Roofing": 3000}
    deadlines = ["As soon as possible", "Within 1-2 weeks", "Within 1 month", "I'm flexible"]
    descriptions = [
        "Replace kitchen sink shutoff valve, you supply valve",
        "Install 2 ceiling fans in bedrooms",
        "Bed bug heat treatment, 2BR apartment",
        "Exterior window wash, 2-story, 20 windows",
        "AC unit not cooling, needs service",
        "Full roof replacement, 1800 sqft",
    ]
    rows = []
    for i in range(90):
        category = categories[i % len(categories)]
        base = bases[category]
        midpoint = base + (i % 7) * 25
        lo = midpoint * 0.7
        hi = midpoint * 1.4
        # final price tracks midpoint with a small deterministic wobble
        final = midpoint * (0.9 + ((i * 13) % 21) / 100.0)
        rows.append({
            "job_id": _sha256_id(1000 + i),
            "service_category": category,
            "service_subtype": "",
            "zip_code": f"{30000 + i:05d}",
            "booking_month": f"2026-{(i % 4) + 1:02d}",
            "job_description": descriptions[i % len(descriptions)],
            "estimate_lo": lo,
            "estimate_hi": hi,
            "original_estimate": midpoint,
            "final_price": final,
            "deadline": deadlines[i % len(deadlines)],
        })
    return pd.DataFrame(rows)
