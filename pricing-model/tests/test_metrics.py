"""Tests for pricing.metrics.

Why these matter: MAPE is the number the whole project is graded on. If the
metric is wrong, every "we beat baseline" claim downstream is wrong too.
"""

from __future__ import annotations

import numpy as np
import pytest

from pricing.metrics import absolute_percentage_error, mape, median_ape


class TestAbsolutePercentageError:
    @pytest.mark.parametrize(
        ("predicted", "actual", "expected"),
        [
            (110, 100, 0.10),
            (90, 100, 0.10),
            (100, 100, 0.0),
            (200, 100, 1.0),
        ],
    )
    def test_computes_relative_error_against_actual(
        self, predicted, actual, expected
    ) -> None:
        assert absolute_percentage_error(predicted, actual) == pytest.approx(expected)

    def test_rejects_non_positive_actual_rather_than_dividing_by_zero(self) -> None:
        with pytest.raises(ValueError, match="positive"):
            absolute_percentage_error(100, 0)


class TestMape:
    def test_averages_per_row_percentage_error(self) -> None:
        # errors are 0.10 and 0.30 -> mean 0.20
        assert mape([110, 130], [100, 100]) == pytest.approx(0.20)

    def test_rejects_length_mismatch(self) -> None:
        with pytest.raises(ValueError, match="length mismatch"):
            mape([100, 200], [100])

    def test_rejects_empty_input(self) -> None:
        with pytest.raises(ValueError, match="empty"):
            mape([], [])

    def test_accepts_numpy_arrays(self) -> None:
        # the eval harness passes numpy arrays, not lists
        result = mape(np.array([110.0, 130.0]), np.array([100.0, 100.0]))
        assert result == pytest.approx(0.20)


class TestMedianApe:
    def test_returns_middle_error_unaffected_by_one_large_outlier(self) -> None:
        # errors: 0.0, 0.10, 5.0 -> median 0.10, while the mean would be ~1.7
        result = median_ape([100, 110, 600], [100, 100, 100])
        assert result == pytest.approx(0.10)
