"""Data adapter: load the HouseAccount pricing CSV into a normalized frame.

Responsibilities kept here (and nowhere else):
- read the raw CSV and coerce types,
- normalize ``service_category`` to canonical title-case,
- guard loudly against accidentally running on synthetic data,
- carve the supervised (priced) subset and a deterministic train/test split.

Feature engineering lives in ``pricing.features``; this layer only produces a
clean, trustworthy frame.
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

# The 18 categories present in the training dataset (title-case canonical form).
DATASET_CATEGORIES: tuple[str, ...] = (
    "Appliance Repair", "Auto", "Chimney", "Cleaning", "Electrical",
    "Exterior", "Flooring", "General Contractor", "Handyman", "HVAC",
    "Landscaping", "Moving", "Painting", "Pest Control", "Plumbing",
    "Pool", "Remodeling", "Roofing",
)

# Kebab/odd-case inputs we still want to land on the canonical title-case label.
# ``str.title()`` mangles acronyms, so the irregulars are listed explicitly.
_CATEGORY_ALIASES: dict[str, str] = {
    "hvac": "HVAC",
}

REQUIRED_COLUMNS: tuple[str, ...] = (
    "job_id", "service_category", "zip_code", "job_description",
    "estimate_lo", "estimate_hi", "original_estimate", "final_price",
)

_NUMERIC_COLUMNS: tuple[str, ...] = (
    "estimate_lo", "estimate_hi", "original_estimate", "final_price",
)

_SYNTHETIC_ID = re.compile(r"^job_\d+$")
_SHA256_ID = re.compile(r"^[0-9a-fA-F]{64}$")


def normalize_category(raw: str) -> str:
    """Map any casing/slug form to the canonical title-case dataset label.

    Examples: ``"plumbing" -> "Plumbing"``, ``"pest-control" -> "Pest Control"``,
    ``"hvac" -> "HVAC"``. Unknown strings pass through title-cased so the model
    can still produce an estimate (with reduced confidence) for novel categories.
    """
    cleaned = raw.strip().replace("-", " ").replace("_", " ")
    collapsed = re.sub(r"\s+", " ", cleaned)
    alias = _CATEGORY_ALIASES.get(collapsed.lower())
    return alias if alias else collapsed.title()


def load_pricing_csv(path: str | Path) -> pd.DataFrame:
    """Load and normalize the pricing CSV. Raises if the file is missing."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"Pricing dataset not found at {path}. Export the Google Sheet to "
            f"CSV and save it there (see README)."
        )

    frame = pd.read_csv(path, dtype={"zip_code": str})
    missing = [c for c in REQUIRED_COLUMNS if c not in frame.columns]
    if missing:
        raise ValueError(f"dataset is missing required columns: {missing}")

    frame["service_category"] = frame["service_category"].map(normalize_category)
    for column in _NUMERIC_COLUMNS:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    return frame


def is_synthetic(frame: pd.DataFrame) -> bool:
    """True if job_ids look generated (``job_000123``) rather than SHA-256.

    The eval harness uses this to refuse to report "real" MAPE numbers against
    fabricated data — fail loud rather than ship a meaningless score.
    """
    ids = frame["job_id"].astype(str)
    synthetic_share = ids.str.match(_SYNTHETIC_ID).mean()
    sha256_share = ids.str.match(_SHA256_ID).mean()
    return bool(synthetic_share > 0.5 or sha256_share < 0.5)


def assert_real(frame: pd.DataFrame) -> None:
    """Raise if the frame appears to be synthetic sample data."""
    if is_synthetic(frame):
        raise ValueError(
            "Refusing to proceed: dataset looks synthetic (job_ids are not "
            "SHA-256 hashes). Drop the real export at data/pricing_real.csv."
        )


def guard_dataset(frame: pd.DataFrame, allow_synthetic: bool = False) -> bool:
    """Gate the harness on data provenance. Returns True iff the data is synthetic.

    Raises when the data is synthetic and the caller has not explicitly opted in
    via ``allow_synthetic``. This is the single chokepoint that prevents fake
    numbers from being reported as real eval results.
    """
    synthetic = is_synthetic(frame)
    if synthetic and not allow_synthetic:
        raise ValueError(
            "Refusing to proceed: dataset looks synthetic (job_ids are not "
            "SHA-256 hashes). Drop the real export at data/pricing_real.csv, or "
            "pass --allow-synthetic to run on fabricated data (results are NOT real)."
        )
    return synthetic


def priced(frame: pd.DataFrame) -> pd.DataFrame:
    """Rows with a known ``final_price`` — the supervised signal."""
    return frame[frame["final_price"].notna()].reset_index(drop=True)


def baseline_midpoints(frame: pd.DataFrame) -> pd.Series:
    """The previous model's point estimate per row — the number we must beat.

    Uses ``original_estimate`` when present, else the midpoint of the estimate
    bounds. This is the baseline prediction the eval compares our model against.
    """
    midpoint = pd.to_numeric(frame["original_estimate"], errors="coerce")
    bounds_mid = (
        pd.to_numeric(frame["estimate_lo"], errors="coerce")
        + pd.to_numeric(frame["estimate_hi"], errors="coerce")
    ) / 2.0
    return midpoint.fillna(bounds_mid)


def split_priced(
    frame: pd.DataFrame, test_frac: float = 0.2, seed: int = 42
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Deterministic train/test split over the priced subset.

    The test split is never seen during training; the harness reports held-out
    MAPE on it so the comparison against baseline is honest.
    """
    if not 0.0 < test_frac < 1.0:
        raise ValueError(f"test_frac must be in (0, 1), got {test_frac}")
    labeled = priced(frame)
    test = labeled.sample(frac=test_frac, random_state=seed)
    train = labeled.drop(test.index)
    return train.reset_index(drop=True), test.reset_index(drop=True)
