"""Data exploration and feature extraction pipeline."""

import pandas as pd
import numpy as np
from pathlib import Path
import json
from typing import Dict, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"


class DataExplorer:
    """Explore and analyze pricing dataset."""

    def __init__(self, csv_path: str = None):
        if csv_path is None:
            csv_path = DATA_DIR / "houseaccount_pricing_sample.csv"
        self.df = pd.read_csv(csv_path)
        self.labeled_df = self.df[self.df["final_price"].notna()].copy()
        logger.info(f"Loaded {len(self.df)} total rows, {len(self.labeled_df)} labeled")

    def summary_stats(self) -> Dict:
        """Compute summary statistics."""
        stats = {
            "total_rows": len(self.df),
            "labeled_rows": len(self.labeled_df),
            "categories": self.df["service_category"].nunique(),
            "unique_zips": self.df["zip_code"].nunique(),
        }

        if len(self.labeled_df) > 0:
            stats["price_stats"] = {
                "mean": float(self.labeled_df["final_price"].mean()),
                "median": float(self.labeled_df["final_price"].median()),
                "std": float(self.labeled_df["final_price"].std()),
                "min": float(self.labeled_df["final_price"].min()),
                "max": float(self.labeled_df["final_price"].max()),
                "q25": float(self.labeled_df["final_price"].quantile(0.25)),
                "q75": float(self.labeled_df["final_price"].quantile(0.75)),
            }

        return stats

    def category_analysis(self) -> Dict:
        """Analyze pricing by category."""
        result = {}
        for cat in self.df["service_category"].unique():
            cat_data = self.labeled_df[self.labeled_df["service_category"] == cat]
            if len(cat_data) > 0:
                result[cat] = {
                    "count": len(cat_data),
                    "avg_price": float(cat_data["final_price"].mean()),
                    "price_range": {
                        "lo": float(cat_data["final_price"].min()),
                        "hi": float(cat_data["final_price"].max()),
                    },
                }
        return result

    def baseline_mape(self) -> Tuple[float, float]:
        """Compute baseline MAPE using original_estimate."""
        # Full dataset MAPE
        full_ape = np.abs(
            (self.labeled_df["original_estimate"] - self.labeled_df["final_price"]) /
            self.labeled_df["final_price"]
        )
        full_mape = full_ape.mean() * 100

        # Real-only MAPE (simulate 27-row subset)
        real_subset = self.labeled_df.sample(min(27, len(self.labeled_df)), random_state=42)
        real_ape = np.abs(
            (real_subset["original_estimate"] - real_subset["final_price"]) /
            real_subset["final_price"]
        )
        real_mape = real_ape.mean() * 100 if len(real_ape) > 0 else 0

        return full_mape, real_mape

    def print_report(self):
        """Print comprehensive analysis report."""
        print("\n" + "="*60)
        print("DATASET EXPLORATION REPORT")
        print("="*60)

        stats = self.summary_stats()
        print(f"\nDataset Size:")
        print(f"  Total rows: {stats['total_rows']}")
        print(f"  Labeled rows (with final_price): {stats['labeled_rows']}")
        print(f"  Label rate: {100*stats['labeled_rows']/stats['total_rows']:.1f}%")
        print(f"  Categories: {stats['categories']}")
        print(f"  Unique ZIP codes: {stats['unique_zips']}")

        if "price_stats" in stats:
            ps = stats["price_stats"]
            print(f"\nPrice Statistics:")
            print(f"  Mean: ${ps['mean']:.2f}")
            print(f"  Median: ${ps['median']:.2f}")
            print(f"  Std Dev: ${ps['std']:.2f}")
            print(f"  Range: ${ps['min']:.2f} - ${ps['max']:.2f}")
            print(f"  IQR: ${ps['q25']:.2f} - ${ps['q75']:.2f}")

        cat_analysis = self.category_analysis()
        print(f"\nCategory Analysis ({len(cat_analysis)} categories):")
        for cat in sorted(cat_analysis.keys(), key=lambda c: cat_analysis[c]["count"], reverse=True)[:5]:
            data = cat_analysis[cat]
            print(f"  {cat}: {data['count']} jobs, avg ${data['avg_price']:.0f}")

        full_mape, real_mape = self.baseline_mape()
        print(f"\nBaseline MAPE (original_estimate):")
        print(f"  Full dataset (277 labeled rows): {full_mape:.2f}%")
        print(f"  Real-only subset (27 rows): {real_mape:.2f}%")
        print(f"\nTarget: Beat 11.6% (full) and 40% (real-only)")
        print("="*60 + "\n")


if __name__ == "__main__":
    explorer = DataExplorer()
    explorer.print_report()
