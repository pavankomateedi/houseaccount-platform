"""Marketplace domain objects.

Kept separate from the message-intelligence models per the PRD's domain-separation
requirement. Mirrors HouseAccount's real flow: a request is matched to vetted,
insured pros who quote within a two-hour window; the homeowner accepts a quote,
which creates a booking; payment happens after completion.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

from ..models import Sentiment


class RequestStatus(StrEnum):
    NEW = "new"
    MATCHED = "matched"
    QUOTED = "quoted"
    BOOKED = "booked"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class QuoteStatus(StrEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"


class Provider(BaseModel):
    id: str
    name: str
    services: list[str]
    coverage_zips: list[str]
    rating: float = Field(ge=0.0, le=5.0)
    vetted: bool = True
    insured: bool = True
    jobs_done: int = 0


class ServiceRequest(BaseModel):
    id: str
    homeowner_id: str
    service_type: str
    zip_code: str
    timing: str | None = None
    notes: str = ""
    status: RequestStatus = RequestStatus.NEW
    source: str = "web"  # "web" or "chat" (engine write-back)
    created_from_conversation_id: str | None = None


class Quote(BaseModel):
    id: str
    request_id: str
    provider_id: str
    amount: float
    quote_window_hours: int = 2  # HouseAccount's two-hour quote window
    status: QuoteStatus = QuoteStatus.PENDING


class Booking(BaseModel):
    id: str
    request_id: str
    provider_id: str
    quote_id: str
    scheduled_time: str | None = None
    status: str = "scheduled"


class Review(BaseModel):
    id: str
    provider_id: str
    homeowner_id: str
    service_type: str
    rating: int = Field(ge=1, le=5)
    sentiment: Sentiment
    text: str
