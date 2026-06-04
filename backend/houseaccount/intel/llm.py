"""Live classifier backed by Claude Opus 4.8.

Forces a structured tool call so the model returns a validated Classification.
The system prompt (instructions + taxonomy) is marked for prompt caching, since
it is identical across every message we classify.
"""

from __future__ import annotations

from typing import Any

from ..config import LIVE_MODEL, get_api_key
from ..models import Category, Classification, Conversation, Sentiment, Urgency
from ..taxonomy import load_services, service_keys

_TOOL_NAME = "record_classification"


def _tool_schema() -> dict[str, Any]:
    return {
        "name": _TOOL_NAME,
        "description": "Record the structured classification of a customer chat conversation.",
        "input_schema": {
            "type": "object",
            "properties": {
                "category": {"type": "string", "enum": [c.value for c in Category]},
                "service_type": {
                    "type": ["string", "null"],
                    "enum": [*service_keys(), None],
                    "description": "Canonical taxonomy key, or null if unclear.",
                },
                "timing": {"type": ["string", "null"]},
                "urgency": {"type": "string", "enum": [u.value for u in Urgency]},
                "property_ref": {"type": ["string", "null"]},
                "pricing_ref": {"type": ["string", "null"]},
                "sentiment": {"type": "string", "enum": [s.value for s in Sentiment]},
                "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                "rationale": {"type": "string"},
            },
            "required": ["category", "urgency", "sentiment", "confidence"],
        },
    }


def _system_blocks() -> list[dict[str, Any]]:
    services = "\n".join(f"- {s.key}: {s.label}" for s in load_services())
    text = (
        "You are HouseAccount's message-intelligence engine. You read a customer "
        "chat conversation between a homeowner and a provider/agent and classify it.\n\n"
        "Categories:\n"
        "- new_request: homeowner wants to book a service\n"
        "- reschedule: change time of an existing booking\n"
        "- cancellation: cancel an existing booking\n"
        "- complaint: dissatisfaction, damage, no-show, refund demand\n"
        "- pricing_question: asking about cost/quote/rate\n"
        "- follow_up: chasing status/update on an existing request\n\n"
        "Extract the service_type using ONLY these canonical keys:\n"
        f"{services}\n\n"
        "Judge urgency (low/medium/high), sentiment (positive/neutral/negative), "
        "and give a calibrated confidence in [0,1]. Always call the "
        f"{_TOOL_NAME} tool."
    )
    return [{"type": "text", "text": text, "cache_control": {"type": "ephemeral"}}]


def _conversation_text(conv: Conversation) -> str:
    return "\n".join(f"{m.sender.value}: {m.text}" for m in conv.messages)


class LiveClassifier:
    """Claude Opus 4.8 classifier. Lazily constructs the client."""

    mode = "live"

    def __init__(self) -> None:
        import anthropic

        key = get_api_key()
        if not key:
            raise RuntimeError(
                "HA_MODE=live requires ANTHROPIC_API_KEY (set it in the environment "
                "or a .env file). Use HA_MODE=mock to run offline."
            )
        self._client = anthropic.Anthropic(api_key=key)
        self._tool = _tool_schema()
        self._system = _system_blocks()

    def classify(self, conv: Conversation) -> Classification:
        # The SDK's overloads expect concrete TypedDicts; our plain dicts are
        # valid at runtime, so we suppress the strict call-overload check here.
        resp = self._client.messages.create(  # type: ignore[call-overload]
            model=LIVE_MODEL,
            max_tokens=512,
            system=self._system,
            tools=[self._tool],
            tool_choice={"type": "tool", "name": _TOOL_NAME},
            messages=[{"role": "user", "content": _conversation_text(conv)}],
        )
        payload = _extract_tool_input(resp)
        return _to_classification(payload)


def _extract_tool_input(resp: Any) -> dict[str, Any]:
    for block in resp.content:
        if getattr(block, "type", None) == "tool_use" and block.name == _TOOL_NAME:
            return dict(block.input)
    raise RuntimeError("Opus did not return the expected tool call")


def _to_classification(payload: dict[str, Any]) -> Classification:
    from ..models import Entities

    return Classification(
        category=Category(payload["category"]),
        entities=Entities(
            service_type=payload.get("service_type"),
            timing=payload.get("timing"),
            urgency=Urgency(payload["urgency"]),
            property_ref=payload.get("property_ref"),
            pricing_ref=payload.get("pricing_ref"),
        ),
        sentiment=Sentiment(payload["sentiment"]),
        confidence=float(payload["confidence"]),
        rationale=str(payload.get("rationale", "")),
    )
