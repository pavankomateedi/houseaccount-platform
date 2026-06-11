"""Tests for pricing.calibration.

The contract is strict: any single OOD condition MUST drop confidence below 0.5.
We assert that as an invariant over a grid, and we replay the shared golden
cases that the JS endpoint is also tested against.
"""

from __future__ import annotations

import itertools

import pytest

from pricing.calibration import (
    PRODUCTION_CATEGORIES,
    calibrate_confidence,
    ood_flags,
)

MEDIAN_INTERVAL = 300.0


class TestOODInvariant:
    @pytest.mark.parametrize(
        ("midpoint", "lo", "hi", "category"),
        [
            (8000, 7500, 8500, "Plumbing"),       # price OOD only
            (600, 50, 1300, "Plumbing"),          # interval OOD only (width 1250 > 900)
            (500, 440, 560, "Roofing"),           # category OOD only
        ],
    )
    def test_any_single_ood_flag_forces_confidence_below_threshold(
        self, midpoint, lo, hi, category
    ) -> None:
        flags = ood_flags(midpoint, lo, hi, category, MEDIAN_INTERVAL)
        assert flags.any
        confidence = calibrate_confidence(midpoint, lo, hi, category, MEDIAN_INTERVAL)
        assert confidence < 0.5

    def test_grid_every_ood_combination_stays_below_threshold(self) -> None:
        # Sweep the three OOD axes; whenever at least one trips, confidence < 0.5.
        for midpoint, width, category in itertools.product(
            [400, 6000], [200, 1500], ["Plumbing", "Pool"]
        ):
            lo = midpoint - width / 2
            hi = midpoint + width / 2
            flags = ood_flags(midpoint, lo, hi, category, MEDIAN_INTERVAL)
            confidence = calibrate_confidence(
                midpoint, lo, hi, category, MEDIAN_INTERVAL
            )
            if flags.any:
                assert confidence < 0.5
            else:
                assert confidence >= 0.5


class TestInDistributionConfidence:
    def test_clean_tight_estimate_is_auto_accept_grade(self) -> None:
        # production category, midpoint < 5k, interval well under 3x median
        confidence = calibrate_confidence(450, 400, 500, "Plumbing", MEDIAN_INTERVAL)
        assert confidence >= 0.75

    def test_confidence_is_clamped_to_unit_interval(self) -> None:
        confidence = calibrate_confidence(300, 299, 301, "HVAC", MEDIAN_INTERVAL)
        assert 0.0 <= confidence <= 1.0

    def test_production_categories_cover_eight_dataset_labels(self) -> None:
        assert len(PRODUCTION_CATEGORIES) == 8


class TestGoldenCases:
    def test_golden_calibration_cases_hold(self, calibration_cases) -> None:
        median_interval = calibration_cases["median_interval"]
        for case in calibration_cases["cases"]:
            confidence = calibrate_confidence(
                case["midpoint"], case["lo"], case["hi"],
                case["category"], median_interval,
            )
            expect = case["expect"]
            if "confidence_min" in expect:
                assert confidence >= expect["confidence_min"], case["name"]
            if "confidence_max" in expect:
                assert confidence <= expect["confidence_max"], case["name"]
            if "flags" in expect:
                flags = ood_flags(
                    case["midpoint"], case["lo"], case["hi"],
                    case["category"], median_interval,
                )
                for axis, value in expect["flags"].items():
                    assert getattr(flags, axis) == value, f"{case['name']}:{axis}"
