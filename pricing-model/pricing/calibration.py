"""Confidence calibration and out-of-distribution (OOD) rules.

Domain layer: pure functions, no I/O, no model objects. The Netlify endpoint
re-implements this exact logic in JS (functions/_lib/calibration.js); both are
covered by the same golden cases so they cannot drift.

Contract (Appendix A): confidence MUST drop below 0.5 when an input is OOD. OOD
means any of:
  1. estimate midpoint  > $5,000        (95th percentile of training data)
  2. interval (hi - lo)  > 3x median observed range
  3. service_category    outside the current production set of 10 verticals

We do not reject or cap OOD inputs; we pass them through with low confidence so
the marketplace can route them.
"""

from __future__ import annotations

from dataclasses import dataclass

OOD_MIDPOINT_USD = 5_000.0
OOD_INTERVAL_MULTIPLE = 3.0

# Highest confidence we will assert for an in-distribution job, and the factor
# applied per OOD flag. The invariant 0.9 * 0.5 = 0.45 < 0.5 guarantees that a
# single OOD flag always pushes confidence below the 0.5 threshold.
_MAX_BASE_CONFIDENCE = 0.9
_MIN_BASE_CONFIDENCE = 0.5
_OOD_PENALTY = 0.5

# The 10 production verticals are kebab slugs; the dataset uses title-case. This
# is the mapping from production slug -> dataset category we treat as in-distro.
# (exterior-cleaning/indoor-cleaning -> Cleaning; irrigation/landscaping-lawn ->
# Landscaping; tick-mosquito-treatment -> Pest Control.) Surfaced in the model
# card because it is a judgment call, not a clean 1:1 mapping.
PRODUCTION_CATEGORIES: frozenset[str] = frozenset(
    {
        "Electrical",
        "Cleaning",
        "Handyman",
        "HVAC",
        "Landscaping",
        "Pest Control",
        "Plumbing",
        "Exterior",
    }
)


@dataclass(frozen=True)
class OODFlags:
    """Which OOD conditions a prediction tripped."""

    price: bool
    interval: bool
    category: bool

    @property
    def any(self) -> bool:
        return self.price or self.interval or self.category


def ood_flags(
    midpoint: float,
    lo: float,
    hi: float,
    category: str,
    median_interval: float,
) -> OODFlags:
    """Evaluate the three OOD conditions for one prediction."""
    return OODFlags(
        price=midpoint > OOD_MIDPOINT_USD,
        interval=(hi - lo) > OOD_INTERVAL_MULTIPLE * median_interval,
        category=category not in PRODUCTION_CATEGORIES,
    )


def _base_confidence(midpoint: float, lo: float, hi: float) -> float:
    """In-distribution confidence graded by relative interval width.

    A tight interval relative to the midpoint means a sharp, trustworthy
    estimate; a wide one means we are unsure even before any OOD flag.
    """
    if midpoint <= 0:
        return _MIN_BASE_CONFIDENCE
    relative_width = (hi - lo) / midpoint
    graded = 0.95 - 0.45 * relative_width
    return max(_MIN_BASE_CONFIDENCE, min(_MAX_BASE_CONFIDENCE, graded))


def calibrate_confidence(
    midpoint: float,
    lo: float,
    hi: float,
    category: str,
    median_interval: float,
) -> float:
    """Final confidence in [0, 1]; < 0.5 whenever any OOD condition holds."""
    confidence = _base_confidence(midpoint, lo, hi)
    flags = ood_flags(midpoint, lo, hi, category, median_interval)
    if flags.price:
        confidence *= _OOD_PENALTY
    if flags.interval:
        confidence *= _OOD_PENALTY
    if flags.category:
        confidence *= _OOD_PENALTY
    return max(0.0, min(1.0, confidence))
