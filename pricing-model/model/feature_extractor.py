"""Feature extraction using Claude API and structured features."""

import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Any
import pickle
import logging
from anthropic import Anthropic

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"

# Production categories for OOD detection
PRODUCTION_CATEGORIES = {
    "electrical", "exterior", "handyman", "hvac", "cleaning",
    "landscaping", "pest-control", "plumbing"
}

client = Anthropic()


class FeatureExtractor:
    """Extract features from pricing data using Claude API."""

    def __init__(self, cache_path: str = None):
        self.cache_path = cache_path or DATA_DIR / "extracted_features.json"
        self.cache = self._load_cache()

    def _load_cache(self) -> Dict:
        """Load cached feature extractions."""
        if Path(self.cache_path).exists():
            with open(self.cache_path, "r") as f:
                logger.info(f"Loaded {len(json.load(f))} cached extractions")
                return json.load(f)
        return {}

    def _save_cache(self):
        """Save extracted features to cache."""
        with open(self.cache_path, "w") as f:
            json.dump(self.cache, f)

    def extract_scope(self, job_description: str) -> Dict[str, Any]:
        """Use Claude to extract scope features from job description."""
        if job_description in self.cache:
            return self.cache[job_description]

        prompt = f"""Extract scope features from this job description for pricing estimation.

Job description: "{job_description}"

Return a JSON object with these fields (all optional, set to null if not found):
- complexity: "low", "medium", or "high"
- scope_size: "small", "medium", or "large" (based on square footage, number of fixtures, etc.)
- materials_provided: true/false/null (whether customer supplies materials)
- urgency: "routine", "expedited", or "emergency"
- fixtures_count: approximate number if applicable (e.g., number of windows, outlets, etc.), null otherwise

Be concise. Return only valid JSON."""

        try:
            message = client.messages.create(
                model="claude-opus-4-7",
                max_tokens=200,
                messages=[{"role": "user", "content": prompt}]
            )
            response_text = message.content[0].text

            # Parse JSON from response
            try:
                features = json.loads(response_text)
            except json.JSONDecodeError:
                # Try to extract JSON if wrapped in markdown
                if "```json" in response_text:
                    json_str = response_text.split("```json")[1].split("```")[0]
                    features = json.loads(json_str)
                elif "```" in response_text:
                    json_str = response_text.split("```")[1].split("```")[0]
                    features = json.loads(json_str)
                else:
                    features = {}

            self.cache[job_description] = features
            return features
        except Exception as e:
            logger.error(f"Error extracting scope: {e}")
            self.cache[job_description] = {}
            return {}

    def encode_categorical(self, df: pd.DataFrame) -> pd.DataFrame:
        """Encode categorical features."""
        result = df.copy()

        # One-hot encode service category
        category_dummies = pd.get_dummies(
            result["service_category"],
            prefix="cat",
            drop_first=True
        )
        result = pd.concat([result, category_dummies], axis=1)

        # One-hot encode deadline
        deadline_dummies = pd.get_dummies(
            result["deadline"],
            prefix="deadline",
            drop_first=True
        )
        result = pd.concat([result, deadline_dummies], axis=1)

        # One-hot encode month
        result["booking_month_numeric"] = pd.to_datetime(
            result["booking_month"]
        ).dt.month

        return result

    def compute_price_ratio(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute price ratio (original_estimate / final_price)."""
        result = df.copy()
        result["price_ratio"] = result["original_estimate"] / (result["final_price"] + 1e-6)
        return result

    def compute_interval_width(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute prediction interval width."""
        result = df.copy()
        result["interval_width"] = result["estimate_hi"] - result["estimate_lo"]
        result["interval_width_ratio"] = result["interval_width"] / (result["estimate_lo"] + 1e-6)
        return result

    def compute_ood_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute out-of-distribution indicator features."""
        result = df.copy()

        # Category OOD (not in production set)
        result["cat_is_prod"] = result["service_category"].str.lower().isin(PRODUCTION_CATEGORIES).astype(int)

        # Price OOD (above $5000)
        result["price_is_high"] = (result["estimate_lo"] > 5000).astype(int)

        # Interval width OOD (compared to median)
        median_interval = result["interval_width"].median()
        result["interval_is_wide"] = (result["interval_width"] > 3 * median_interval).astype(int)

        return result

    def extract_all_features(self, csv_path: str = None) -> pd.DataFrame:
        """Extract all features from dataset."""
        if csv_path is None:
            csv_path = DATA_DIR / "houseaccount_pricing_sample.csv"

        df = pd.read_csv(csv_path)
        logger.info(f"Loaded {len(df)} rows")

        # Extract scope from descriptions (sample for speed)
        logger.info("Extracting scope features from descriptions...")
        # For demo, we'll add simple heuristic features instead of calling Claude for every row
        # In production, this would be batched and cached
        scope_features = []
        for desc in df["job_description"]:
            features = {
                "complexity": "medium",  # simplified
                "scope_size": "medium",
                "materials_provided": None,
                "urgency": "routine",
                "fixtures_count": None
            }
            scope_features.append(features)

        # Add scope features as columns
        df["complexity"] = [f.get("complexity") for f in scope_features]
        df["scope_size"] = [f.get("scope_size") for f in scope_features]
        df["urgency"] = [f.get("urgency") for f in scope_features]

        # Encode categorical features
        logger.info("Encoding categorical features...")
        df = self.encode_categorical(df)
        df = self.compute_interval_width(df)
        df = self.compute_ood_features(df)

        # For labeled data, compute price ratio
        labeled_df = df[df["final_price"].notna()].copy()
        labeled_df = self.compute_price_ratio(labeled_df)

        logger.info(f"Extracted features for {len(df)} rows")

        return df, labeled_df

    def get_model_features(self, df: pd.DataFrame) -> List[str]:
        """Get list of feature columns for modeling."""
        feature_cols = []

        # Categorical encodings (one-hot)
        feature_cols.extend([col for col in df.columns if col.startswith("cat_")])

        # Deadline encodings
        feature_cols.extend([col for col in df.columns if col.startswith("deadline_")])

        # Numerical features
        feature_cols.extend([
            "booking_month_numeric",
            "interval_width",
            "interval_width_ratio",
            "cat_is_prod",
            "price_is_high",
            "interval_is_wide",
        ])

        # Remove columns that don't exist
        feature_cols = [col for col in feature_cols if col in df.columns]

        return feature_cols


if __name__ == "__main__":
    extractor = FeatureExtractor()
    df, labeled_df = extractor.extract_all_features()

    print(f"\nExtracted {len(df)} rows")
    print(f"Feature columns: {len(extractor.get_model_features(df))}")
    print(f"Labeled rows: {len(labeled_df)}")

    # Save for later use
    df.to_csv(DATA_DIR / "features_all.csv", index=False)
    labeled_df.to_csv(DATA_DIR / "features_labeled.csv", index=False)
    logger.info("Saved feature CSVs")
