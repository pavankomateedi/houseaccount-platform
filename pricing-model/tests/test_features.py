"""Tests for pricing.features.

Feature parity with the JS endpoint depends on these extractors being exact, so
we pin the scope-signal behavior and the vector layout precisely.
"""

from __future__ import annotations

import math

import pytest

from pricing.features import (
    DEADLINE_VOCAB,
    NUMERIC_FEATURES,
    FeatureSpec,
    build_feature_row,
    extract_scope,
)

SPEC = FeatureSpec(
    category_vocab=("Cleaning", "Plumbing", "Roofing"),
    deadline_vocab=DEADLINE_VOCAB,
    default_estimate=300.0,
    default_interval=200.0,
)


class TestExtractScope:
    def test_counts_words_and_largest_number(self) -> None:
        scope = extract_scope("Exterior window wash, 2-story, 20 windows")
        assert scope["desc_word_count"] == 6.0
        assert scope["max_number"] == 20.0

    def test_detects_homeowner_supplied_materials(self) -> None:
        assert extract_scope("Replace valve, you supply valve")["materials_supplied"] == 1.0
        assert extract_scope("Replace valve")["materials_supplied"] == 0.0

    def test_handles_empty_and_missing_description(self) -> None:
        assert extract_scope("")["desc_word_count"] == 0.0
        assert extract_scope(None)["max_number"] == 0.0


class TestBuildFeatureRow:
    def test_one_hot_encodes_known_category(self) -> None:
        row = build_feature_row({"service_category": "Plumbing"}, SPEC)
        assert row["cat::Plumbing"] == 1.0
        assert row["cat::Cleaning"] == 0.0

    def test_unknown_category_leaves_all_dummies_zero(self) -> None:
        row = build_feature_row({"service_category": "Moving"}, SPEC)
        assert all(row[f"cat::{c}"] == 0.0 for c in SPEC.category_vocab)

    def test_falls_back_to_default_estimate_when_absent(self) -> None:
        row = build_feature_row({"service_category": "Plumbing"}, SPEC)
        assert row["log_original_estimate"] == pytest.approx(math.log1p(300.0))

    def test_uses_estimate_bounds_midpoint_when_no_original(self) -> None:
        row = build_feature_row(
            {"service_category": "Plumbing", "estimate_lo": 100, "estimate_hi": 300},
            SPEC,
        )
        assert row["log_original_estimate"] == pytest.approx(math.log1p(200.0))

    def test_accepts_request_style_estimate_bounds(self) -> None:
        # API requests carry original_estimate_lo/hi, not estimate_lo/hi.
        row = build_feature_row(
            {
                "service_category": "Plumbing",
                "original_estimate_lo": 100,
                "original_estimate_hi": 500,
            },
            SPEC,
        )
        assert row["log_estimate_interval"] == pytest.approx(math.log1p(400.0))


class TestFeatureSpec:
    def test_feature_order_is_numeric_then_categories_then_deadlines(self) -> None:
        order = SPEC.feature_order
        assert order[: len(NUMERIC_FEATURES)] == list(NUMERIC_FEATURES)
        assert len(order) == len(NUMERIC_FEATURES) + 3 + len(DEADLINE_VOCAB)

    def test_roundtrips_through_dict(self) -> None:
        assert FeatureSpec.from_dict(SPEC.to_dict()) == SPEC
