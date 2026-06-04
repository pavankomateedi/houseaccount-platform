"""Compute per-conversation insights and aggregate operations statistics.

This is the data behind the Insights/Triage console: each conversation paired
with its engine insight, plus rolled-up counts that an ops team would act on.
"""

from __future__ import annotations

from collections import Counter

from pydantic import BaseModel

from .intel.engine import Classifier, analyze
from .models import Conversation, Insight


class InsightView(BaseModel):
    conversation: Conversation
    insight: Insight


class AggregateStats(BaseModel):
    total: int
    by_category: dict[str, int]
    by_sentiment: dict[str, int]
    by_urgency: dict[str, int]
    by_route: dict[str, int]
    by_action: dict[str, int]
    top_services: list[tuple[str, int]]
    complaint_rate: float
    human_review_rate: float
    avg_confidence: float


def compute_views(convs: list[Conversation], classifier: Classifier) -> list[InsightView]:
    return [
        InsightView(conversation=c, insight=analyze(c, classifier))
        for c in convs
    ]


def aggregate(views: list[InsightView]) -> AggregateStats:
    n = len(views)
    insights: list[Insight] = [v.insight for v in views]
    cats = Counter(i.classification.category.value for i in insights)
    sents = Counter(i.classification.sentiment.value for i in insights)
    urgs = Counter(i.classification.entities.urgency.value for i in insights)
    routes = Counter(i.route.value for i in insights)
    actions = Counter(i.action.value for i in insights)
    services = Counter(
        i.classification.entities.service_type
        for i in insights
        if i.classification.entities.service_type
    )
    complaints = cats.get("complaint", 0)
    human_review = routes.get("human_review", 0)
    avg_conf = sum(i.classification.confidence for i in insights) / n if n else 0.0

    return AggregateStats(
        total=n,
        by_category=dict(cats),
        by_sentiment=dict(sents),
        by_urgency=dict(urgs),
        by_route=dict(routes),
        by_action=dict(actions),
        top_services=services.most_common(5),
        complaint_rate=round(complaints / n, 3) if n else 0.0,
        human_review_rate=round(human_review / n, 3) if n else 0.0,
        avg_confidence=round(avg_conf, 3),
    )
