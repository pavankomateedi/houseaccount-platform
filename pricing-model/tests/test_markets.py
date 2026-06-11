"""Tests for pricing.markets — ZIP-to-metro mapping and sampling."""

from __future__ import annotations

from random import Random

import pytest

from pricing.markets import MARKETS, market_for_zip, sample_zip, weighted_market


class TestMarketForZip:
    @pytest.mark.parametrize(
        ("zip_code", "expected"),
        [
            ("10023", "New York, NY"),
            ("11201", "New York, NY"),
            ("75001", "Dallas, TX"),
            ("94105", "SF Bay Area, CA"),
            ("95014", "SF Bay Area, CA"),
            ("99999", None),
            ("00000", None),
        ],
    )
    def test_maps_zip_prefix_to_market(self, zip_code, expected) -> None:
        assert market_for_zip(zip_code) == expected


def test_sample_zip_returns_a_serviced_zip_in_its_market() -> None:
    rng = Random(0)
    for market in MARKETS:
        for _ in range(25):
            zip_code = sample_zip(market, rng)
            assert zip_code in market.zips
            assert market_for_zip(zip_code) == market.name


def test_weighted_market_returns_a_known_market() -> None:
    assert weighted_market(Random(1)) in MARKETS
