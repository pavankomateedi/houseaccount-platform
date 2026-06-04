"""Marketplace business logic: matching, quoting, booking, and engine write-backs.

Matching uses deterministic eligibility first (service + coverage), then ranks by
rating — per the PRD ("deterministic eligibility rules first, AI ranking later").
Pricing is a deterministic table, not a model call (Rule 5: code answers).
"""

from __future__ import annotations

from ..models import Insight
from .models import Booking, Provider, Quote, QuoteStatus, RequestStatus, ServiceRequest
from .store import MarketplaceStore

# Deterministic base price per service (USD). Real pricing would be dynamic; this
# keeps quotes reproducible for the demo and tests.
_BASE_PRICE: dict[str, float] = {
    "house_cleaning": 120, "deep_cleaning": 220, "furniture_assembly": 90,
    "tv_mounting": 110, "help_moving": 250, "heavy_lifting": 140,
    "junk_removal": 160, "handyman": 95, "plumbing": 180, "electrical": 175,
    "appliance_repair": 150, "painting": 300, "yard_work": 130, "smart_home": 140,
}
_DEFAULT_PRICE = 120.0


def eligible_providers(store: MarketplaceStore, service_type: str, zip_code: str) -> list[Provider]:
    """Vetted providers that serve this service in this area, best-rated first."""
    matches = [
        p
        for p in store.providers.values()
        if service_type in p.services and zip_code in p.coverage_zips
    ]
    return sorted(matches, key=lambda p: (p.rating, p.jobs_done), reverse=True)


def create_request(
    store: MarketplaceStore,
    *,
    homeowner_id: str,
    service_type: str,
    zip_code: str,
    timing: str | None = None,
    notes: str = "",
    source: str = "web",
    conversation_id: str | None = None,
) -> ServiceRequest:
    req = ServiceRequest(
        id=store.next_id("req"),
        homeowner_id=homeowner_id,
        service_type=service_type,
        zip_code=zip_code,
        timing=timing,
        notes=notes,
        source=source,
        created_from_conversation_id=conversation_id,
    )
    if eligible_providers(store, service_type, zip_code):
        req.status = RequestStatus.MATCHED
    store.requests[req.id] = req
    return req


def quote_for(provider: Provider, service_type: str) -> float:
    """Deterministic quote: base price nudged by rating (higher rated, slight premium)."""
    base = _BASE_PRICE.get(service_type, _DEFAULT_PRICE)
    premium = 1.0 + (provider.rating - 4.5) * 0.04
    return round(base * premium, 2)


def generate_quotes(store: MarketplaceStore, request_id: str, top_n: int = 3) -> list[Quote]:
    req = store.requests[request_id]
    providers = eligible_providers(store, req.service_type, req.zip_code)[:top_n]
    quotes: list[Quote] = []
    for p in providers:
        q = Quote(
            id=store.next_id("quote"),
            request_id=req.id,
            provider_id=p.id,
            amount=quote_for(p, req.service_type),
        )
        store.quotes[q.id] = q
        quotes.append(q)
    if quotes:
        req.status = RequestStatus.QUOTED
    return quotes


def accept_quote(
    store: MarketplaceStore, quote_id: str, scheduled_time: str | None = None
) -> Booking:
    quote = store.quotes[quote_id]
    quote.status = QuoteStatus.ACCEPTED
    # Decline sibling quotes on the same request.
    for q in store.quotes.values():
        if q.request_id == quote.request_id and q.id != quote.id:
            q.status = QuoteStatus.DECLINED
    req = store.requests[quote.request_id]
    req.status = RequestStatus.BOOKED
    booking = Booking(
        id=store.next_id("booking"),
        request_id=req.id,
        provider_id=quote.provider_id,
        quote_id=quote.id,
        scheduled_time=scheduled_time or req.timing,
    )
    store.bookings[booking.id] = booking
    return booking


def apply_insight(
    store: MarketplaceStore, insight: Insight, *, homeowner_id: str, zip_code: str
) -> str | None:
    """Write an engine insight back into the marketplace.

    Only the low-risk CREATE_JOB action auto-creates a request, and only with a
    known service type. Everything else (cancellations, complaints, anything
    routed to human review) is intentionally left for a human — matching the
    PRD's automation-vs-oversight split. Returns a created request id, if any.
    """
    from ..models import ActionType, Route

    if insight.route is Route.HUMAN_REVIEW:
        return None
    if insight.action is not ActionType.CREATE_JOB:
        return None
    service_type = insight.classification.entities.service_type
    if service_type is None:
        return None
    req = create_request(
        store,
        homeowner_id=homeowner_id,
        service_type=service_type,
        zip_code=zip_code,
        timing=insight.classification.entities.timing,
        notes="Auto-created from customer chat by message-intelligence engine.",
        source="chat",
        conversation_id=insight.conversation_id,
    )
    return req.id
