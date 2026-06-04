"""Deterministic routing + action rules.

Per the PRD: orchestration logic stays explicit and auditable, NOT embedded in
model inference. The model classifies; this module decides what happens next.
The same rules produce the corpus's ground-truth route and the engine's live
route, so the eval measures whether the model recovered the fields that drive
the right decision.
"""

from __future__ import annotations

from ..models import ActionType, Category, Route, Sentiment, Urgency

# Below this confidence we always ask a human, regardless of category.
CONFIDENCE_FLOOR = 0.55

# Categories that are intrinsically high-risk (money / retention / trust).
_HIGH_RISK = {Category.COMPLAINT, Category.CANCELLATION}

_ACTION_BY_CATEGORY: dict[Category, ActionType] = {
    Category.NEW_REQUEST: ActionType.CREATE_JOB,
    Category.RESCHEDULE: ActionType.UPDATE_BOOKING,
    Category.CANCELLATION: ActionType.CANCEL_BOOKING,
    Category.COMPLAINT: ActionType.ESCALATE,
    Category.PRICING_QUESTION: ActionType.SEND_PRICING_INFO,
    Category.FOLLOW_UP: ActionType.SEND_REMINDER,
}


def action_for(category: Category) -> ActionType:
    return _ACTION_BY_CATEGORY[category]


def decide_route(
    category: Category,
    urgency: Urgency,
    sentiment: Sentiment,
    confidence: float,
) -> tuple[Route, str | None]:
    """Return (route, escalation_reason). reason is None when auto."""
    if confidence < CONFIDENCE_FLOOR:
        return Route.HUMAN_REVIEW, "low_confidence"
    if category in _HIGH_RISK:
        return Route.HUMAN_REVIEW, f"high_risk_category:{category.value}"
    if sentiment is Sentiment.NEGATIVE:
        return Route.HUMAN_REVIEW, "negative_sentiment"
    if urgency is Urgency.HIGH:
        return Route.HUMAN_REVIEW, "high_urgency"
    return Route.AUTO, None
