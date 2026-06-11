"""Tests for pricing.data — loading, normalization, and the synthetic guard."""

from __future__ import annotations

import pytest

import pandas as pd

from pricing.data import (
    assert_real,
    baseline_midpoints,
    is_synthetic,
    load_pricing_csv,
    normalize_category,
    priced,
    split_priced,
)


class TestNormalizeCategory:
    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ("plumbing", "Plumbing"),
            ("PLUMBING", "Plumbing"),
            ("pest-control", "Pest Control"),
            ("hvac", "HVAC"),
            ("HVAC", "HVAC"),
            ("  General Contractor  ", "General Contractor"),
            ("solar-panels", "Solar Panels"),  # unknown passes through title-cased
        ],
    )
    def test_maps_any_casing_or_slug_to_canonical_label(self, raw, expected) -> None:
        assert normalize_category(raw) == expected


class TestLoadPricingCsv:
    def test_normalizes_category_column_on_read(self, real_csv) -> None:
        frame = load_pricing_csv(real_csv)
        assert set(frame["service_category"]) <= {
            "Plumbing", "Pest Control", "HVAC", "Roofing", "Cleaning"
        }

    def test_coerces_price_columns_to_numeric(self, real_csv) -> None:
        frame = load_pricing_csv(real_csv)
        # blanks in final_price must become NaN floats, not the string ""
        assert frame["final_price"].dtype.kind == "f"
        assert frame["original_estimate"].dtype.kind in "fi"

    def test_raises_when_file_missing(self, tmp_path) -> None:
        with pytest.raises(FileNotFoundError, match="not found"):
            load_pricing_csv(tmp_path / "nope.csv")


class TestSyntheticGuard:
    def test_flags_generated_ids_as_synthetic(self, synthetic_csv) -> None:
        assert is_synthetic(load_pricing_csv(synthetic_csv)) is True

    def test_accepts_sha256_ids_as_real(self, real_csv) -> None:
        assert is_synthetic(load_pricing_csv(real_csv)) is False

    def test_assert_real_raises_on_synthetic(self, synthetic_csv) -> None:
        with pytest.raises(ValueError, match="synthetic"):
            assert_real(load_pricing_csv(synthetic_csv))

    def test_assert_real_passes_on_real(self, real_csv) -> None:
        assert_real(load_pricing_csv(real_csv))  # does not raise


class TestPricedAndSplit:
    def test_priced_keeps_only_rows_with_final_price(self, real_csv) -> None:
        frame = load_pricing_csv(real_csv)
        labeled = priced(frame)
        assert len(labeled) == 10
        assert labeled["final_price"].notna().all()

    def test_split_is_deterministic_for_a_seed(self, real_csv) -> None:
        frame = load_pricing_csv(real_csv)
        a_train, a_test = split_priced(frame, test_frac=0.2, seed=7)
        b_train, b_test = split_priced(frame, test_frac=0.2, seed=7)
        assert list(a_test["job_id"]) == list(b_test["job_id"])

    def test_split_has_no_leakage_between_train_and_test(self, real_csv) -> None:
        frame = load_pricing_csv(real_csv)
        train, test = split_priced(frame, test_frac=0.2, seed=7)
        assert set(train["job_id"]).isdisjoint(set(test["job_id"]))
        assert len(train) + len(test) == 10


class TestBaselineMidpoints:
    def test_prefers_original_estimate(self) -> None:
        frame = pd.DataFrame(
            {"original_estimate": [150.0], "estimate_lo": [100.0], "estimate_hi": [300.0]}
        )
        assert baseline_midpoints(frame).iloc[0] == 150.0

    def test_falls_back_to_bounds_midpoint_when_estimate_missing(self) -> None:
        frame = pd.DataFrame(
            {"original_estimate": [None], "estimate_lo": [100.0], "estimate_hi": [300.0]}
        )
        assert baseline_midpoints(frame).iloc[0] == 200.0
