"""Shared domain models for HouseAccount.

These types are the contract between the corpus generator, the message-intelligence
engine, the marketplace, and the eval harness. The LLM (or mock) produces a
`Classification`; deterministic code turns that into a routed `Insight`.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class Category(StrEnum):
    """Intent of a customer chat conversation."""

    NEW_REQUEST = "new_request"
    RESCHEDULE = "reschedule"
    CANCELLATION = "cancellation"
    COMPLAINT = "complaint"
    PRICING_QUESTION = "pricing_question"
    FOLLOW_UP = "follow_up"


class Urgency(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Sentiment(StrEnum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


class Route(StrEnum):
    """Where the conversation goes next. Decided by deterministic rules."""

    AUTO = "auto"
    HUMAN_REVIEW = "human_review"


class ActionType(StrEnum):
    """The actionable output suggested for the conversation."""

    CREATE_JOB = "create_job"
    UPDATE_BOOKING = "update_booking"
    CANCEL_BOOKING = "cancel_booking"
    ESCALATE = "escalate"
    SEND_PRICING_INFO = "send_pricing_info"
    SEND_REMINDER = "send_reminder"


class Sender(StrEnum):
    HOMEOWNER = "homeowner"
    PROVIDER = "provider"


class Message(BaseModel):
    sender: Sender
    text: str


class Entities(BaseModel):
    """Structured facts pulled from the conversation."""

    service_type: str | None = Field(
        default=None, description="Taxonomy key, e.g. 'house_cleaning'."
    )
    timing: str | None = Field(default=None, description="When the work is wanted, free text.")
    urgency: Urgency = Urgency.LOW
    property_ref: str | None = Field(default=None, description="Property descriptor, if mentioned.")
    pricing_ref: str | None = Field(default=None, description="Any price/quote mentioned.")


class GroundTruth(BaseModel):
    """Labels baked into the synthetic corpus; the eval scores against these.

    ``timing``/``pricing_ref`` hold the value actually woven into the message
    text, or None when the conversation never mentions one. The eval scores those
    entities as presence-agreement, so the engine is rewarded for staying silent
    when there is nothing to extract.
    """

    category: Category
    service_type: str | None
    timing: str | None
    pricing_ref: str | None
    urgency: Urgency
    sentiment: Sentiment
    route: Route


class Conversation(BaseModel):
    """A homeowner ↔ service-provider chat thread that HouseAccount has visibility
    into. The platform sits in the middle and reads every thread for oversight."""

    id: str
    homeowner_id: str
    zip_code: str
    messages: list[Message]
    provider_id: str | None = None
    provider_name: str | None = None
    ground_truth: GroundTruth | None = None


class Classification(BaseModel):
    """What the engine (LLM or mock) infers from the conversation text alone."""

    category: Category
    entities: Entities
    sentiment: Sentiment
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str = ""


class Insight(BaseModel):
    """Classification + the deterministic routing/action decision."""

    conversation_id: str
    classification: Classification
    route: Route
    action: ActionType
    escalation_reason: str | None = None
    # Marketplace write-back id, if any (e.g. created service-request id).
    linked_request_id: str | None = None
