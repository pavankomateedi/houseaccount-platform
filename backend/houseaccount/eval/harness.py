"""Eval harness: run the engine over a labeled set and gate against thresholds."""

from __future__ import annotations

from pydantic import BaseModel

from ..intel.engine import Classifier, analyze
from ..models import Conversation, Insight
from .metrics import accuracy, macro_f1

# The success bar from DECISIONS.md. Gated fields must clear these.
THRESHOLDS: dict[str, float] = {
    "category_f1": 0.85,
    "route_f1": 0.90,
    "entity_score": 0.80,
    "sentiment_accuracy": 0.80,
}


class EvalReport(BaseModel):
    mode: str
    n: int
    category_f1: float
    route_f1: float
    entity_score: float
    sentiment_accuracy: float
    urgency_accuracy: float  # reported, not gated
    passed: bool
    failures: list[str]

    def summary(self) -> str:
        status = "PASS" if self.passed else "FAIL"
        lines = [
            f"[{status}] eval mode={self.mode} n={self.n}",
            f"  category_f1        = {self.category_f1:.3f}  (>= {THRESHOLDS['category_f1']})",
            f"  route_f1           = {self.route_f1:.3f}  (>= {THRESHOLDS['route_f1']})",
            f"  entity_score       = {self.entity_score:.3f}  (>= {THRESHOLDS['entity_score']})",
            f"  sentiment_accuracy = {self.sentiment_accuracy:.3f}  "
            f"(>= {THRESHOLDS['sentiment_accuracy']})",
            f"  urgency_accuracy   = {self.urgency_accuracy:.3f}  (ungated)",
        ]
        if self.failures:
            lines.append("  failures: " + ", ".join(self.failures))
        return "\n".join(lines)


def _entity_score(convs: list[Conversation], preds: list[Insight]) -> float:
    """Per-conversation entity correctness, averaged.

    service_type: exact key match (0.5). timing / pricing_ref: presence
    agreement (0.25 each) — correct extraction includes correctly extracting
    nothing when the conversation mentions nothing.
    """
    if not convs:
        return 0.0
    total = 0.0
    for conv, insight in zip(convs, preds, strict=True):
        gt = conv.ground_truth
        assert gt is not None, "golden conversations must be labeled"
        ent = insight.classification.entities
        service_ok = 1.0 if ent.service_type == gt.service_type else 0.0
        timing_ok = 1.0 if (ent.timing is None) == (gt.timing is None) else 0.0
        pricing_ok = 1.0 if (ent.pricing_ref is None) == (gt.pricing_ref is None) else 0.0
        total += 0.5 * service_ok + 0.25 * timing_ok + 0.25 * pricing_ok
    return total / len(convs)


def evaluate(convs: list[Conversation], classifier: Classifier) -> EvalReport:
    for c in convs:
        if c.ground_truth is None:
            raise ValueError(f"conversation {c.id} has no ground truth")

    insights = [analyze(c, classifier) for c in convs]
    gt = [c.ground_truth for c in convs]

    category_f1 = macro_f1(
        [g.category.value for g in gt],  # type: ignore[union-attr]
        [i.classification.category.value for i in insights],
    )
    route_f1 = macro_f1(
        [g.route.value for g in gt],  # type: ignore[union-attr]
        [i.route.value for i in insights],
    )
    sentiment_acc = accuracy(
        [g.sentiment.value for g in gt],  # type: ignore[union-attr]
        [i.classification.sentiment.value for i in insights],
    )
    urgency_acc = accuracy(
        [g.urgency.value for g in gt],  # type: ignore[union-attr]
        [i.classification.entities.urgency.value for i in insights],
    )
    entity_score = _entity_score(convs, insights)

    measured = {
        "category_f1": category_f1,
        "route_f1": route_f1,
        "entity_score": entity_score,
        "sentiment_accuracy": sentiment_acc,
    }
    failures = [k for k, v in measured.items() if v < THRESHOLDS[k]]

    return EvalReport(
        mode=classifier.mode,
        n=len(convs),
        category_f1=category_f1,
        route_f1=route_f1,
        entity_score=entity_score,
        sentiment_accuracy=sentiment_acc,
        urgency_accuracy=urgency_acc,
        passed=not failures,
        failures=failures,
    )
