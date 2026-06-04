"""Marketplace flow: eligibility, quoting, booking, and engine write-back."""

import pytest

from houseaccount.intel.engine import analyze
from houseaccount.intel.mock import MockClassifier
from houseaccount.intel.router import action_for
from houseaccount.marketplace import service
from houseaccount.marketplace.models import QuoteStatus, RequestStatus
from houseaccount.marketplace.store import MarketplaceStore
from houseaccount.models import (
    Category,
    Classification,
    Conversation,
    Entities,
    Insight,
    Message,
    Route,
    Sender,
    Sentiment,
    Urgency,
)


@pytest.fixture
def store() -> MarketplaceStore:
    return MarketplaceStore()


def test_eligibility_requires_service_and_coverage(store: MarketplaceStore):
    # pro-03 cleans in 94114 but does not cover 94103.
    in_area = service.eligible_providers(store, "house_cleaning", "94114")
    assert any(p.id == "pro-03" for p in in_area)
    assert not service.eligible_providers(store, "house_cleaning", "94103")


def test_eligibility_ranks_by_rating(store: MarketplaceStore):
    ranked = service.eligible_providers(store, "handyman", "94110")
    assert ranked, "expected handyman providers in 94110"
    ratings = [p.rating for p in ranked]
    assert ratings == sorted(ratings, reverse=True)


def test_full_flow_request_to_booking(store: MarketplaceStore):
    req = service.create_request(
        store, homeowner_id="ho-1", service_type="plumbing", zip_code="94110"
    )
    assert req.status is RequestStatus.MATCHED
    quotes = service.generate_quotes(store, req.id)
    assert quotes
    assert store.requests[req.id].status is RequestStatus.QUOTED
    booking = service.accept_quote(store, quotes[0].id, scheduled_time="Saturday 10am")
    assert booking.scheduled_time == "Saturday 10am"
    assert store.requests[req.id].status is RequestStatus.BOOKED
    assert store.quotes[quotes[0].id].status is QuoteStatus.ACCEPTED
    # Sibling quotes declined.
    for q in quotes[1:]:
        assert store.quotes[q.id].status is QuoteStatus.DECLINED


def _insight(category: Category, route: Route, service_type: str | None) -> Insight:
    return Insight(
        conversation_id="conv-x",
        classification=Classification(
            category=category,
            entities=Entities(service_type=service_type, urgency=Urgency.LOW),
            sentiment=Sentiment.NEUTRAL,
            confidence=0.9,
        ),
        route=route,
        action=action_for(category),
    )


def test_apply_insight_creates_job_for_auto_new_request(store: MarketplaceStore):
    ins = _insight(Category.NEW_REQUEST, Route.AUTO, "handyman")
    req_id = service.apply_insight(store, ins, homeowner_id="ho-9", zip_code="94110")
    assert req_id is not None
    created = store.requests[req_id]
    assert created.source == "chat"
    assert created.created_from_conversation_id == "conv-x"


def test_apply_insight_skips_human_review(store: MarketplaceStore):
    ins = _insight(Category.NEW_REQUEST, Route.HUMAN_REVIEW, "handyman")
    assert service.apply_insight(store, ins, homeowner_id="ho-9", zip_code="94110") is None


def test_apply_insight_skips_when_service_unknown(store: MarketplaceStore):
    ins = _insight(Category.NEW_REQUEST, Route.AUTO, None)
    assert service.apply_insight(store, ins, homeowner_id="ho-9", zip_code="94110") is None


def test_engine_to_marketplace_endtoend(store: MarketplaceStore):
    # A realistic new-request chat should flow all the way to a created job.
    conv = Conversation(
        id="conv-e2e",
        homeowner_id="ho-7",
        zip_code="94110",
        messages=[
            Message(
                sender=Sender.HOMEOWNER,
                text="Hi, I need help with general handyman at my townhouse.",
            ),
            Message(sender=Sender.PROVIDER, text="Happy to help!"),
            Message(sender=Sender.HOMEOWNER, text="Sounds good."),
        ],
    )
    insight = analyze(conv, MockClassifier())
    assert insight.classification.category is Category.NEW_REQUEST
    req_id = service.apply_insight(
        store, insight, homeowner_id=conv.homeowner_id, zip_code=conv.zip_code
    )
    assert req_id is not None
