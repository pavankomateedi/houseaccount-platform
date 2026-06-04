"""Scoring primitives. Hand-rolled to avoid a scikit-learn dependency on 3.14."""

from __future__ import annotations

from collections.abc import Sequence


def accuracy(y_true: Sequence[str], y_pred: Sequence[str]) -> float:
    if not y_true:
        return 0.0
    correct = sum(1 for t, p in zip(y_true, y_pred, strict=True) if t == p)
    return correct / len(y_true)


def macro_f1(y_true: Sequence[str], y_pred: Sequence[str]) -> float:
    """Unweighted mean of per-class F1 over all labels present in truth or pred."""
    labels = set(y_true) | set(y_pred)
    if not labels:
        return 0.0
    f1s: list[float] = []
    for label in labels:
        tp = sum(1 for t, p in zip(y_true, y_pred, strict=True) if t == label and p == label)
        fp = sum(1 for t, p in zip(y_true, y_pred, strict=True) if t != label and p == label)
        fn = sum(1 for t, p in zip(y_true, y_pred, strict=True) if t == label and p != label)
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
        f1s.append(f1)
    return sum(f1s) / len(f1s)
