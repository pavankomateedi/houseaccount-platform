"""Message-intelligence engine: classification + deterministic routing.

The classifier (mock or live) does judgment; ``decide_route`` / ``action_for``
do the deterministic orchestration. The result is an auditable Insight.
"""

from __future__ import annotations

from typing import Protocol

from ..config import get_mode
from ..models import Classification, Conversation, Insight
from .router import action_for, decide_route


class Classifier(Protocol):
    mode: str

    def classify(self, conv: Conversation) -> Classification: ...


def get_classifier(mode: str | None = None) -> Classifier:
    """Return the classifier for the given mode (defaults to env HA_MODE)."""
    resolved = mode or get_mode()
    if resolved == "live":
        from .llm import LiveClassifier

        return LiveClassifier()
    from .mock import MockClassifier

    return MockClassifier()


def analyze(conv: Conversation, classifier: Classifier) -> Insight:
    cls = classifier.classify(conv)
    route, reason = decide_route(
        cls.category, cls.entities.urgency, cls.sentiment, cls.confidence
    )
    return Insight(
        conversation_id=conv.id,
        classification=cls,
        route=route,
        action=action_for(cls.category),
        escalation_reason=reason,
    )


def analyze_all(convs: list[Conversation], classifier: Classifier) -> list[Insight]:
    return [analyze(c, classifier) for c in convs]
