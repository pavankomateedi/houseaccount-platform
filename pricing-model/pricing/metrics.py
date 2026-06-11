"""Pricing accuracy metrics. Pure functions, no I/O.

All errors are reported as fractions (0.116 means 11.6%). Callers format for
display. The supervised target throughout the project is ``final_price``; a
"prediction" is a single point estimate (a midpoint) in USD.
"""

from __future__ import annotations

from collections.abc import Sequence
from statistics import median


def absolute_percentage_error(predicted: float, actual: float) -> float:
    """APE for a single pair: |predicted - actual| / actual.

    ``actual`` is a real provider charge and must be positive; a non-positive
    actual is a data error we surface rather than silently divide by.
    """
    if actual <= 0:
        raise ValueError(f"actual price must be positive, got {actual}")
    return abs(predicted - actual) / actual


def _percentage_errors(
    predicted: Sequence[float], actual: Sequence[float]
) -> list[float]:
    if len(predicted) != len(actual):
        raise ValueError(
            f"length mismatch: {len(predicted)} predictions, {len(actual)} actuals"
        )
    if len(predicted) == 0:
        raise ValueError("cannot compute error over an empty set")
    return [absolute_percentage_error(p, a) for p, a in zip(predicted, actual)]


def mape(predicted: Sequence[float], actual: Sequence[float]) -> float:
    """Mean absolute percentage error as a fraction."""
    errors = _percentage_errors(predicted, actual)
    return sum(errors) / len(errors)


def median_ape(predicted: Sequence[float], actual: Sequence[float]) -> float:
    """Median absolute percentage error as a fraction.

    Reported alongside MAPE because the brief quotes both (median APE 8.3%); the
    gap between them signals how much a few hard rows dominate the mean.
    """
    return median(_percentage_errors(predicted, actual))
