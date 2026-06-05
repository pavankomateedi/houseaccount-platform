"""Inference server for pricing model predictions."""

import sys
import json
from pathlib import Path
import logging
import pandas as pd
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent
MODEL_PATH = PROJECT_ROOT / "model" / "pricing_model.pkl"
DATA_DIR = PROJECT_ROOT / "data"

# Load model on startup
from train_model import PricingModel
from feature_extractor import FeatureExtractor

model = None
extractor = None
feature_cols = None


def load_model():
    """Load trained model."""
    global model, extractor, feature_cols
    if model is None:
        model = PricingModel.load(MODEL_PATH)
        extractor = FeatureExtractor()
        # Load feature names from a previously saved CSV
        df_sample = pd.read_csv(DATA_DIR / "features_all.csv")
        feature_cols = extractor.get_model_features(df_sample)
    return model, extractor, feature_cols


def predict(request_data: dict) -> dict:
    """Make a pricing prediction."""
    try:
        model, extractor, feature_cols = load_model()

        # Validate required fields
        required = ["job_id", "service_category", "zip_code", "job_description"]
        for field in required:
            if field not in request_data:
                return {"error": f"{field} required"}

        # Create dataframe for prediction
        df_request = pd.DataFrame([{
            "service_category": request_data["service_category"],
            "zip_code": request_data["zip_code"],
            "job_description": request_data["job_description"],
            "service_subtype": request_data.get("service_subtype", ""),
            "deadline": request_data.get("deadline", "I'm flexible"),
            "booking_month": request_data.get("booking_month", "2026-04"),
            "estimate_lo": request_data.get("original_estimate_lo", 500),
            "estimate_hi": request_data.get("original_estimate_hi", 1500),
            "interval_width": request_data.get("original_estimate_hi", 1500) - request_data.get("original_estimate_lo", 500),
            "cat_is_prod": 1 if request_data["service_category"].lower() in {"electrical", "exterior", "handyman", "hvac", "cleaning", "landscaping", "pest control", "plumbing"} else 0,
            "price_is_high": 1 if request_data.get("original_estimate", 500) > 5000 else 0,
            "interval_is_wide": 0,  # Will be computed
            "booking_month_numeric": int(request_data.get("booking_month", "2026-04").split("-")[1]),
        }])

        # Encode categorical features (simplified)
        for col in feature_cols:
            if col not in df_request.columns:
                df_request[col] = 0

        # Make prediction
        X = df_request[feature_cols].fillna(0)
        X_scaled = model.scaler.transform(X)
        log_pred = model.model.predict(X_scaled)[0]
        midpoint = np.exp(log_pred)

        # Generate interval
        interval = 500  # Simplified interval
        lo = max(midpoint - interval / 2, 0)
        hi = midpoint + interval / 2

        # Calibrate confidence
        confidence = model._calibrate_confidence(df_request, interval)

        return {
            "ok": True,
            "job_id": request_data["job_id"],
            "estimate_lo": float(lo),
            "estimate_hi": float(hi),
            "estimate_midpoint": float(midpoint),
            "confidence": float(confidence),
            "model_version": model.model_version,
        }

    except Exception as e:
        logger.error(f"Prediction error: {e}")
        return {"error": str(e)}


if __name__ == "__main__":
    # Test from command line
    test_request = {
        "job_id": "test_001",
        "service_category": "Plumbing",
        "zip_code": "78704",
        "job_description": "Replace water heater",
    }
    result = predict(test_request)
    print(json.dumps(result, indent=2))
