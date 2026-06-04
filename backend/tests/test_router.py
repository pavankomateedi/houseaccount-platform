"""The router is the actionable decision; these tests pin WHY each route happens."""

from houseaccount.intel.router import CONFIDENCE_FLOOR, action_for, decide_route
from houseaccount.models import ActionType, Category, Route, Sentiment, Urgency


def test_low_confidence_always_goes_to_human():
    route, reason = decide_route(
        Category.NEW_REQUEST, Urgency.LOW, Sentiment.NEUTRAL, CONFIDENCE_FLOOR - 0.01
    )
    assert route is Route.HUMAN_REVIEW
    assert reason == "low_confidence"


def test_complaints_escalate_even_when_confident_and_positive():
    # A complaint is high-risk regardless of how the model scored sentiment.
    route, reason = decide_route(Category.COMPLAINT, Urgency.LOW, Sentiment.POSITIVE, 0.99)
    assert route is Route.HUMAN_REVIEW
    assert reason and reason.startswith("high_risk_category")


def test_negative_sentiment_forces_review():
    route, reason = decide_route(Category.FOLLOW_UP, Urgency.LOW, Sentiment.NEGATIVE, 0.9)
    assert route is Route.HUMAN_REVIEW
    assert reason == "negative_sentiment"


def test_high_urgency_forces_review():
    route, reason = decide_route(Category.NEW_REQUEST, Urgency.HIGH, Sentiment.NEUTRAL, 0.9)
    assert route is Route.HUMAN_REVIEW
    assert reason == "high_urgency"


def test_routine_new_request_is_automated():
    route, reason = decide_route(Category.NEW_REQUEST, Urgency.LOW, Sentiment.NEUTRAL, 0.9)
    assert route is Route.AUTO
    assert reason is None


def test_action_mapping_is_total():
    for category in Category:
        assert isinstance(action_for(category), ActionType)
