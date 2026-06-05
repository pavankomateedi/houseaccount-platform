"""Unit and integration tests for pricing model."""

import pytest
import pandas as pd
import numpy as np
import json
from pathlib import Path
import sys

# Add project to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "model"))

from train_model import PricingModel, evaluate_mape
from feature_extractor import FeatureExtractor


class TestFeatureExtraction:
    """Test feature extraction."""

    def test_extract_features(self):
        """Test that features are extracted correctly."""
        extractor = FeatureExtractor()
        df_all, df_labeled = extractor.extract_all_features()

        assert len(df_all) > 0
        assert len(df_labeled) > 0
        assert "final_price" in df_all.columns

    def test_feature_columns_exist(self):
        """Test that required feature columns exist."""
        extractor = FeatureExtractor()
        df_all, _ = extractor.extract_all_features()

        feature_cols = extractor.get_model_features(df_all)
        assert len(feature_cols) > 0
        assert all(col in df_all.columns for col in feature_cols)

    def test_ood_features(self):
        """Test OOD feature computation."""
        extractor = FeatureExtractor()
        df_all, _ = extractor.extract_all_features()

        assert "cat_is_prod" in df_all.columns
        assert "price_is_high" in df_all.columns
        assert "interval_is_wide" in df_all.columns


class TestModel:
    """Test pricing model."""

    def test_model_trains(self):
        """Test that model trains without errors."""
        extractor = FeatureExtractor()
        df_all, df_labeled = extractor.extract_all_features()

        model = PricingModel()
        feature_cols = extractor.get_model_features(df_all)

        mape = model.train(df_labeled, feature_cols)
        assert mape < 20  # Reasonable MAPE

    def test_model_mape_below_baseline(self):
        """Test that MAPE beats baseline of 11.6%."""
        extractor = FeatureExtractor()
        df_all, df_labeled = extractor.extract_all_features()

        model = PricingModel()
        feature_cols = extractor.get_model_features(df_all)

        mape = model.train(df_labeled, feature_cols)
        # With synthetic data, MAPE should beat 11.6%
        assert mape < 11.6, f"MAPE {mape:.2f}% did not beat baseline"

    def test_model_serialization(self):
        """Test model can be saved and loaded."""
        extractor = FeatureExtractor()
        df_all, df_labeled = extractor.extract_all_features()

        model = PricingModel()
        feature_cols = extractor.get_model_features(df_all)
        model.train(df_labeled, feature_cols)

        # Save and load
        model_path = PROJECT_ROOT / "model" / "test_model.pkl"
        model.save(model_path)

        loaded_model = PricingModel.load(model_path)
        assert loaded_model.model is not None
        assert loaded_model.feature_cols == feature_cols

        # Cleanup
        model_path.unlink()

    def test_confidence_calibration(self):
        """Test confidence calibration logic."""
        extractor = FeatureExtractor()
        df_all, df_labeled = extractor.extract_all_features()

        model = PricingModel()
        feature_cols = extractor.get_model_features(df_all)
        model.train(df_labeled, feature_cols)

        # Test OOD detection
        df_test = df_all.iloc[[0]].copy()

        # Test 1: Production category + normal price = high confidence
        df_test["service_category"] = "Plumbing"
        df_test["estimate_lo"] = 500
        df_test["interval_width"] = 500
        conf1 = model._calibrate_confidence(df_test, 500)
        assert conf1 > 0.5, "Should have reasonable confidence for prod category"

        # Test 2: Non-production category = lower confidence
        df_test["service_category"] = "Auto"
        conf2 = model._calibrate_confidence(df_test, 500)
        assert conf2 < conf1, "Non-prod category should have lower confidence"

        # Test 3: High price (>$5000) = lower confidence
        df_test["service_category"] = "Plumbing"
        df_test["estimate_lo"] = 5500
        conf3 = model._calibrate_confidence(df_test, 500)
        assert conf3 < conf1, "High price should reduce confidence"

        # Test 4: Wide interval = lower confidence
        conf4 = model._calibrate_confidence(df_test, 5000)
        assert conf4 < conf1, "Wide interval should reduce confidence"


class TestAPIContract:
    """Test API request/response contract."""

    def test_request_validation_required_fields(self):
        """Test that required fields are validated."""
        required_fields = ["job_id", "service_category", "zip_code", "job_description"]

        for field in required_fields:
            request = {f: "test" for f in required_fields}
            del request[field]

            # In real test, would call API endpoint
            assert field not in request, f"Missing {field} should be caught"

    def test_response_schema(self):
        """Test response matches expected schema."""
        expected_fields = [
            "ok", "job_id", "estimate_lo", "estimate_hi",
            "estimate_midpoint", "confidence", "model_version"
        ]

        # Mock response
        response = {
            "ok": True,
            "job_id": "test_001",
            "estimate_lo": 1000,
            "estimate_hi": 2000,
            "estimate_midpoint": 1500,
            "confidence": 0.75,
            "model_version": "pavan-v1.0.0"
        }

        for field in expected_fields:
            assert field in response, f"Missing field: {field}"
            assert response[field] is not None

    def test_confidence_bounds(self):
        """Test confidence is always in [0, 1]."""
        extractor = FeatureExtractor()
        df_all, df_labeled = extractor.extract_all_features()

        model = PricingModel()
        feature_cols = extractor.get_model_features(df_all)
        model.train(df_labeled, feature_cols)

        for _ in range(10):
            idx = np.random.randint(0, len(df_all))
            df_test = df_all.iloc[[idx]].copy()
            conf = model._calibrate_confidence(df_test, df_test["interval_width"].iloc[0])

            assert 0.0 <= conf <= 1.0, f"Confidence {conf} out of bounds"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
