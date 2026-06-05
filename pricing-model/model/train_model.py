"""Train pricing model and calibrate confidence."""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple, Dict, Any
import pickle
import logging
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
MODEL_DIR = PROJECT_ROOT / "model"

PRODUCTION_CATEGORIES = {
    "electrical", "exterior", "handyman", "hvac", "cleaning",
    "landscaping", "pest-control", "plumbing"
}


class PricingModel:
    """Ridge regression pricing model with confidence calibration."""

    def __init__(self):
        self.model = Ridge(alpha=1.0)
        self.scaler = StandardScaler()
        self.feature_cols = None
        self.median_interval_width = None
        self.model_version = "pavan-v1.0.0"

    def train(self, df: pd.DataFrame, feature_cols: list, test_size: float = 0.2):
        """Train the pricing model."""
        logger.info(f"Training on {len(df)} labeled rows")

        X = df[feature_cols].fillna(0)
        y = np.log(df["final_price"])  # Log transform to reduce outlier sensitivity

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42
        )

        logger.info(f"Train set: {len(X_train)}, Test set: {len(X_test)}")

        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        # Train model
        self.model.fit(X_train_scaled, y_train)

        # Evaluate
        y_pred = self.model.predict(X_test_scaled)
        y_pred_exp = np.exp(y_pred)
        y_test_exp = np.exp(y_test)

        mape = np.mean(np.abs((y_pred_exp - y_test_exp) / y_test_exp)) * 100
        logger.info(f"Test MAPE: {mape:.2f}%")

        self.feature_cols = feature_cols
        self.median_interval_width = df["interval_width"].median()

        return mape

    def predict(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate pricing prediction with confidence."""
        if self.feature_cols is None:
            raise ValueError("Model not trained yet")

        X = df[self.feature_cols].fillna(0)
        X_scaled = self.scaler.transform(X)

        # Predict log price
        log_pred = self.model.predict(X_scaled)[0]
        midpoint = np.exp(log_pred)

        # Generate interval
        interval_width = df["interval_width"].iloc[0]
        lo = midpoint - interval_width / 2
        hi = midpoint + interval_width / 2

        # Calculate confidence
        confidence = self._calibrate_confidence(df, interval_width)

        return {
            "estimate_lo": lo,
            "estimate_hi": hi,
            "estimate_midpoint": midpoint,
            "confidence": confidence,
        }

    def _calibrate_confidence(self, df: pd.DataFrame, interval_width: float) -> float:
        """Calibrate confidence based on OOD signals."""
        category = df["service_category"].iloc[0]
        midpoint = df["estimate_lo"].iloc[0] + interval_width / 2
        is_wide = interval_width > 3 * self.median_interval_width

        # Base confidence
        confidence = 0.8

        # Reduce for OOD category
        if category.lower() not in PRODUCTION_CATEGORIES:
            confidence *= 0.6

        # Reduce for high price
        if midpoint > 5000:
            confidence *= 0.6

        # Reduce for wide interval
        if is_wide:
            confidence *= 0.7

        # Clamp to [0, 1]
        return max(0.0, min(1.0, confidence))

    def save(self, path: str = None):
        """Save model to disk."""
        if path is None:
            path = MODEL_DIR / "pricing_model.pkl"
        with open(path, "wb") as f:
            pickle.dump(self, f)
        logger.info(f"Saved model to {path}")

    @staticmethod
    def load(path: str = None):
        """Load model from disk."""
        if path is None:
            path = MODEL_DIR / "pricing_model.pkl"
        with open(path, "rb") as f:
            model = pickle.load(f)
        logger.info(f"Loaded model from {path}")
        return model


def evaluate_mape(df: pd.DataFrame, pred_col: str = "estimate_midpoint", actual_col: str = "final_price") -> float:
    """Compute MAPE between predictions and actuals."""
    df_eval = df[df[actual_col].notna()].copy()
    ape = np.abs((df_eval[pred_col] - df_eval[actual_col]) / df_eval[actual_col])
    mape = np.mean(ape) * 100
    return mape


if __name__ == "__main__":
    from feature_extractor import FeatureExtractor

    # Extract features
    extractor = FeatureExtractor()
    df_all, df_labeled = extractor.extract_all_features()

    # Train model
    model = PricingModel()
    feature_cols = extractor.get_model_features(df_all)

    test_mape = model.train(df_labeled, feature_cols)
    logger.info(f"Final test MAPE: {test_mape:.2f}%")

    # Predict on full labeled set to compute blended MAPE
    X = df_labeled[feature_cols].fillna(0)
    X_scaled = model.scaler.transform(X)
    y_pred_log = model.model.predict(X_scaled)
    df_labeled["estimate_midpoint"] = np.exp(y_pred_log)

    blended_mape = evaluate_mape(df_labeled)
    logger.info(f"Blended MAPE on full set: {blended_mape:.2f}%")

    # Save model
    model.save()

    print(f"\nModel Training Complete")
    print(f"  Test MAPE: {test_mape:.2f}%")
    print(f"  Blended MAPE: {blended_mape:.2f}%")
    print(f"  Target: <11.6%")
