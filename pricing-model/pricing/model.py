"""Pricing model: quantile linear regression on log-price.

Three quantile regressors (low/median/high) over standardized engineered
features predict log(final_price); exponentiating gives an asymmetric price
interval and a midpoint. The whole model is linear, so it serializes to a small
JSON artifact (per-quantile coefficients + a standardizer) that the JS endpoint
evaluates as a dot product — no Python at request time.

Layer: application/infra. Depends inward on features (engineering) and
calibration (domain rule); the endpoint depends only on the exported JSON.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import QuantileRegressor

from pricing.calibration import calibrate_confidence
from pricing.features import FeatureSpec, baseline_midpoint, build_matrix, fit_spec

_QUANTILES = {"lo": 0.1, "mid": 0.5, "hi": 0.9}


def _baselines(frame: pd.DataFrame, spec: FeatureSpec) -> np.ndarray:
    """Per-row baseline midpoint the model corrects against."""
    return np.array(
        [baseline_midpoint(record, spec) for record in frame.to_dict("records")],
        dtype=float,
    )


@dataclass(frozen=True)
class _LinearModel:
    coef: np.ndarray
    intercept: float

    def predict_log(self, standardized: np.ndarray) -> np.ndarray:
        return standardized @ self.coef + self.intercept


@dataclass(frozen=True)
class Standardizer:
    """Zero-mean/unit-scale transform; constant features get scale 1."""

    mean: np.ndarray
    scale: np.ndarray

    def apply(self, matrix: np.ndarray) -> np.ndarray:
        return (matrix - self.mean) / self.scale


class PricingModel:
    def __init__(
        self,
        spec: FeatureSpec,
        standardizer: Standardizer,
        quantile_models: dict[str, _LinearModel],
        median_predicted_interval: float,
        model_version: str,
    ) -> None:
        self.spec = spec
        self.standardizer = standardizer
        self.quantile_models = quantile_models
        self.median_predicted_interval = median_predicted_interval
        self.model_version = model_version

    # ---- training -------------------------------------------------------
    @classmethod
    def fit(
        cls,
        train_frame: pd.DataFrame,
        model_version: str,
        alpha: float = 0.001,
    ) -> "PricingModel":
        """Fit on the priced training rows. ``final_price`` must be present."""
        spec = fit_spec(train_frame)
        matrix = build_matrix(train_frame, spec)
        # Target is the log-ratio of the actual price to the baseline estimate.
        # The model learns a correction to the baseline rather than the price
        # from scratch, so it anchors at (and rarely loses to) a strong baseline.
        final_price = train_frame["final_price"].to_numpy(dtype=float)
        baselines = _baselines(train_frame, spec)
        target = np.log(final_price) - np.log(baselines)

        mean = matrix.mean(axis=0)
        scale = matrix.std(axis=0)
        scale[scale == 0.0] = 1.0
        standardizer = Standardizer(mean=mean, scale=scale)
        standardized = standardizer.apply(matrix)

        quantile_models: dict[str, _LinearModel] = {}
        for name, quantile in _QUANTILES.items():
            regressor = QuantileRegressor(
                quantile=quantile, alpha=alpha, solver="highs"
            )
            regressor.fit(standardized, target)
            quantile_models[name] = _LinearModel(
                coef=regressor.coef_, intercept=float(regressor.intercept_)
            )

        model = cls(
            spec=spec,
            standardizer=standardizer,
            quantile_models=quantile_models,
            median_predicted_interval=1.0,  # placeholder; set below
            model_version=model_version,
        )
        predictions = model.predict_frame(train_frame)
        interval = float(
            (predictions["estimate_hi"] - predictions["estimate_lo"]).median()
        )
        model.median_predicted_interval = max(interval, 1.0)
        return model

    # ---- inference ------------------------------------------------------
    def predict_frame(self, frame: pd.DataFrame) -> pd.DataFrame:
        """Predict lo/hi/midpoint/confidence for every row."""
        standardized = self.standardizer.apply(build_matrix(frame, self.spec))
        baselines = _baselines(frame, self.spec)
        # Each quantile predicts a log-ratio; price = baseline * exp(ratio).
        bounds = {
            name: baselines * np.exp(model.predict_log(standardized))
            for name, model in self.quantile_models.items()
        }
        # Quantile crossing is possible with separate fits; enforce lo<=mid<=hi.
        stacked = np.sort(
            np.vstack([bounds["lo"], bounds["mid"], bounds["hi"]]).T, axis=1
        )
        lo, mid, hi = stacked[:, 0], stacked[:, 1], stacked[:, 2]

        categories = frame["service_category"].astype(str).to_numpy()
        confidence = np.array(
            [
                calibrate_confidence(
                    mid[i], lo[i], hi[i], categories[i],
                    self.median_predicted_interval,
                )
                for i in range(len(frame))
            ]
        )
        return pd.DataFrame(
            {
                "estimate_lo": lo,
                "estimate_hi": hi,
                "estimate_midpoint": mid,
                "confidence": confidence,
            }
        )

    # ---- serialization --------------------------------------------------
    def to_dict(self) -> dict:
        return {
            "model_version": self.model_version,
            "target": "log_ratio",
            "feature_order": self.spec.feature_order,
            "spec": self.spec.to_dict(),
            "standardizer": {
                "mean": self.standardizer.mean.tolist(),
                "scale": self.standardizer.scale.tolist(),
            },
            "quantiles": {
                name: {
                    "coef": model.coef.tolist(),
                    "intercept": model.intercept,
                }
                for name, model in self.quantile_models.items()
            },
            "median_predicted_interval": self.median_predicted_interval,
        }

    def save_json(self, path: str | Path) -> None:
        Path(path).write_text(json.dumps(self.to_dict(), indent=2))

    @classmethod
    def from_dict(cls, payload: dict) -> "PricingModel":
        standardizer = Standardizer(
            mean=np.array(payload["standardizer"]["mean"], dtype=float),
            scale=np.array(payload["standardizer"]["scale"], dtype=float),
        )
        quantile_models = {
            name: _LinearModel(
                coef=np.array(entry["coef"], dtype=float),
                intercept=float(entry["intercept"]),
            )
            for name, entry in payload["quantiles"].items()
        }
        return cls(
            spec=FeatureSpec.from_dict(payload["spec"]),
            standardizer=standardizer,
            quantile_models=quantile_models,
            median_predicted_interval=float(payload["median_predicted_interval"]),
            model_version=payload["model_version"],
        )

    @classmethod
    def load_json(cls, path: str | Path) -> "PricingModel":
        return cls.from_dict(json.loads(Path(path).read_text()))
