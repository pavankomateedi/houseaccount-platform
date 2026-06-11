"""Tests for pricing.model — the training/inference pipeline.

These verify the pipeline's invariants (ordered intervals, valid confidence,
serialization fidelity), not accuracy; accuracy is the eval harness's job and
requires the real dataset.
"""

from __future__ import annotations

import numpy as np

from pricing.model import PricingModel


class TestPredict:
    def test_intervals_are_ordered_and_positive(self, trainable_frame) -> None:
        model = PricingModel.fit(trainable_frame, model_version="test-v0")
        predictions = model.predict_frame(trainable_frame)
        assert (predictions["estimate_lo"] > 0).all()
        assert (predictions["estimate_lo"] <= predictions["estimate_midpoint"]).all()
        assert (predictions["estimate_midpoint"] <= predictions["estimate_hi"]).all()

    def test_confidence_is_within_unit_interval(self, trainable_frame) -> None:
        model = PricingModel.fit(trainable_frame, model_version="test-v0")
        confidence = model.predict_frame(trainable_frame)["confidence"]
        assert confidence.between(0.0, 1.0).all()

    def test_non_production_category_gets_low_confidence(self, trainable_frame) -> None:
        model = PricingModel.fit(trainable_frame, model_version="test-v0")
        roofing = trainable_frame[trainable_frame["service_category"] == "Roofing"]
        confidence = model.predict_frame(roofing)["confidence"]
        # Roofing is outside the production set -> every row must be < 0.5
        assert (confidence < 0.5).all()


class TestSerialization:
    def test_json_roundtrip_reproduces_predictions(self, trainable_frame, tmp_path) -> None:
        model = PricingModel.fit(trainable_frame, model_version="test-v0")
        path = tmp_path / "model.json"
        model.save_json(path)
        reloaded = PricingModel.load_json(path)

        original = model.predict_frame(trainable_frame)
        restored = reloaded.predict_frame(trainable_frame)
        np.testing.assert_allclose(
            original.to_numpy(), restored.to_numpy(), rtol=1e-9
        )

    def test_artifact_carries_feature_order_and_interval(self, trainable_frame) -> None:
        model = PricingModel.fit(trainable_frame, model_version="test-v0")
        payload = model.to_dict()
        assert payload["feature_order"] == model.spec.feature_order
        assert payload["median_predicted_interval"] > 0
