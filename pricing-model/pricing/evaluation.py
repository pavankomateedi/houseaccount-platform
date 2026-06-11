"""Baseline-vs-model evaluation (application layer).

Produces the three comparison views the harness gates on. Kept in the package
(not the eval/ scripts) so it is importable and unit-tested, and reused by both
run_eval.py (the CLI gate) and export_ui.py (the validation UI).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from pricing.data import baseline_midpoints, priced, split_priced
from pricing.metrics import mape, median_ape
from pricing.model import PricingModel

PUBLISHED_BLENDED_BASELINE = 0.116


@dataclass(frozen=True)
class Scored:
    label: str
    n: int
    baseline_mape: float
    model_mape: float
    baseline_median: float
    model_median: float

    @property
    def beats_baseline(self) -> bool:
        return self.model_mape < self.baseline_mape


def _score(label: str, predictions, baseline, actual) -> Scored:
    actual = np.asarray(actual, dtype=float)
    return Scored(
        label=label,
        n=len(actual),
        baseline_mape=mape(baseline, actual),
        model_mape=mape(predictions, actual),
        baseline_median=median_ape(baseline, actual),
        model_median=median_ape(predictions, actual),
    )


def evaluate(
    frame: pd.DataFrame,
    *,
    version: str,
    seed: int = 42,
    test_frac: float = 0.2,
    real_threshold: float = 0.25,
) -> tuple[list[Scored], PricingModel]:
    """Return (scored views, full-fit model). See run_eval.py for the gate."""
    labeled = priced(frame)

    # 1. Blended: full-fit, scored on all priced rows (the submission view).
    full_model = PricingModel.fit(labeled, model_version=version)
    full_pred = full_model.predict_frame(labeled)["estimate_midpoint"].to_numpy()
    full_base = baseline_midpoints(labeled).to_numpy(dtype=float)
    full_actual = labeled["final_price"].to_numpy(dtype=float)
    blended = _score("blended (full)", full_pred, full_base, full_actual)

    # 2. Held-out: train on train split, score on the unseen test split.
    train, test = split_priced(frame, test_frac=test_frac, seed=seed)
    heldout_model = PricingModel.fit(train, model_version=version)
    test_pred = heldout_model.predict_frame(test)["estimate_midpoint"].to_numpy()
    test_base = baseline_midpoints(test).to_numpy(dtype=float)
    test_actual = test["final_price"].to_numpy(dtype=float)
    heldout = _score("held-out", test_pred, test_base, test_actual)

    # 3. Held-out "real-like": test rows whose baseline APE is large.
    base_ape = np.abs(test_base - test_actual) / test_actual
    mask = base_ape >= real_threshold
    results = [blended, heldout]
    if mask.sum() >= 5:
        results.append(
            _score(
                f"held-out real (APE>={real_threshold:.0%})",
                test_pred[mask], test_base[mask], test_actual[mask],
            )
        )
    return results, full_model
