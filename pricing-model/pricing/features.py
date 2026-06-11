"""Feature engineering for the pricing model.

The feature set is fully described by a ``FeatureSpec`` (category/deadline
vocabularies + fallback constants). That spec is serialized into model.json so
the JS endpoint (functions/_lib/features.js) can rebuild identical vectors — the
spec is the single source of truth that keeps the two implementations in sync.

Scope signals are extracted from ``job_description`` with deliberately simple,
language-agnostic regexes so the JS mirror is a faithful copy. We extract:
- word count (proxy for job complexity / detail),
- the largest number mentioned (quantities: "20 windows", "50-gallon", "2BR"),
- whether the homeowner is supplying materials (shifts price down).
"""

from __future__ import annotations

import math
import re
from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd

# Canonical numeric features, in fixed order. JS mirrors this list by name.
NUMERIC_FEATURES: tuple[str, ...] = (
    "log_original_estimate",
    "log_estimate_interval",
    "booking_month_num",
    "log_desc_word_count",
    "log_max_number",
    "materials_supplied",
)

DEADLINE_VOCAB: tuple[str, ...] = (
    "As soon as possible",
    "Within 1-2 weeks",
    "Within 1 month",
    "I'm flexible",
)

_MATERIALS_SUPPLIED = re.compile(
    r"\b(you supply|i supply|i'll supply|i provide|i'll provide|owner provides?|"
    r"customer provides?|supply the|provided by (?:owner|customer|homeowner))\b",
    re.IGNORECASE,
)
_NUMBER = re.compile(r"\d+(?:\.\d+)?")


@dataclass(frozen=True)
class FeatureSpec:
    """Everything needed to turn a booking record into a feature vector."""

    category_vocab: tuple[str, ...]
    deadline_vocab: tuple[str, ...]
    default_estimate: float
    default_interval: float

    @property
    def feature_order(self) -> list[str]:
        return [
            *NUMERIC_FEATURES,
            *(f"cat::{c}" for c in self.category_vocab),
            *(f"deadline::{d}" for d in self.deadline_vocab),
        ]

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict) -> "FeatureSpec":
        return cls(
            category_vocab=tuple(payload["category_vocab"]),
            deadline_vocab=tuple(payload["deadline_vocab"]),
            default_estimate=float(payload["default_estimate"]),
            default_interval=float(payload["default_interval"]),
        )


def extract_scope(description: object) -> dict[str, float]:
    """Pull scope signals from a free-text job description."""
    text = "" if description is None or (isinstance(description, float) and math.isnan(description)) else str(description)
    words = text.split()
    numbers = [float(n) for n in _NUMBER.findall(text)]
    return {
        "desc_word_count": float(len(words)),
        "max_number": max(numbers) if numbers else 0.0,
        "materials_supplied": 1.0 if _MATERIALS_SUPPLIED.search(text) else 0.0,
    }


def _resolve_estimate(record: dict, spec: FeatureSpec) -> tuple[float, float]:
    """Return (midpoint, interval) from the record, falling back to spec defaults.

    Requests may omit the previous-model estimate entirely; training rows always
    have it. Both paths land here so features are identical.
    """
    # Training rows use estimate_lo/hi; API requests use original_estimate_lo/hi.
    lo = _to_float(record.get("estimate_lo"))
    if lo is None:
        lo = _to_float(record.get("original_estimate_lo"))
    hi = _to_float(record.get("estimate_hi"))
    if hi is None:
        hi = _to_float(record.get("original_estimate_hi"))
    midpoint = _to_float(record.get("original_estimate"))

    if midpoint is None and lo is not None and hi is not None:
        midpoint = (lo + hi) / 2.0
    if midpoint is None:
        midpoint = spec.default_estimate

    if lo is not None and hi is not None:
        interval = max(hi - lo, 0.0)
    else:
        interval = spec.default_interval
    return midpoint, interval


def baseline_midpoint(record: dict, spec: FeatureSpec) -> float:
    """The previous-model midpoint the model anchors its correction to.

    Same resolution as feature building (original_estimate -> bounds mid ->
    spec default), so the model and endpoint agree on the anchor.
    """
    midpoint, _ = _resolve_estimate(record, spec)
    return midpoint


def build_feature_row(record: dict, spec: FeatureSpec) -> dict[str, float]:
    """Build the named feature dict for a single booking record."""
    midpoint, interval = _resolve_estimate(record, spec)
    scope = extract_scope(record.get("job_description"))
    booking_month = _booking_month_number(record.get("booking_month"))

    row: dict[str, float] = {
        "log_original_estimate": math.log1p(max(midpoint, 0.0)),
        "log_estimate_interval": math.log1p(interval),
        "booking_month_num": float(booking_month),
        "log_desc_word_count": math.log1p(scope["desc_word_count"]),
        "log_max_number": math.log1p(scope["max_number"]),
        "materials_supplied": scope["materials_supplied"],
    }

    category = str(record.get("service_category", ""))
    for known in spec.category_vocab:
        row[f"cat::{known}"] = 1.0 if category == known else 0.0

    deadline = str(record.get("deadline", ""))
    for known in spec.deadline_vocab:
        row[f"deadline::{known}"] = 1.0 if deadline == known else 0.0

    return row


def build_matrix(frame: pd.DataFrame, spec: FeatureSpec) -> np.ndarray:
    """Build the (n_rows, n_features) matrix in ``spec.feature_order``."""
    order = spec.feature_order
    rows = [build_feature_row(record, spec) for record in frame.to_dict("records")]
    return np.array([[row[name] for name in order] for row in rows], dtype=float)


def fit_spec(frame: pd.DataFrame) -> FeatureSpec:
    """Derive a FeatureSpec from training data (vocab + fallback medians)."""
    categories = tuple(sorted(frame["service_category"].dropna().unique()))
    midpoint = pd.to_numeric(frame["original_estimate"], errors="coerce")
    interval = pd.to_numeric(frame["estimate_hi"], errors="coerce") - pd.to_numeric(
        frame["estimate_lo"], errors="coerce"
    )
    return FeatureSpec(
        category_vocab=categories,
        deadline_vocab=DEADLINE_VOCAB,
        default_estimate=float(midpoint.median()),
        default_interval=float(interval.median()),
    )


def _to_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(result) else result


def _booking_month_number(booking_month: object) -> int:
    """Month 1-12 from a 'YYYY-MM' string; 0 when absent/unparseable."""
    if not booking_month:
        return 0
    match = re.search(r"-(\d{2})$", str(booking_month))
    return int(match.group(1)) if match else 0
