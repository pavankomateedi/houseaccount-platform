"""Deterministic, text-only heuristic classifier (mock mode).

This is a real classifier — it reads only the conversation text and never the
ground-truth label. That is what makes the offline eval meaningful: the mock has
to actually recover category / service / sentiment / urgency from cues, exactly
like the live model does. It is also the CI-safe path (no network, no API key).
"""

from __future__ import annotations

import re

from ..models import Category, Classification, Conversation, Entities, Sentiment, Urgency
from ..taxonomy import SERVICE_KEYWORDS, load_services

# Category signals. Order encodes tie-break priority (most specific/risky first).
_CATEGORY_SIGNALS: list[tuple[Category, list[str]]] = [
    (
        # Complaint-SPECIFIC cues only. Generic negative words (refund, frustrated,
        # disappointing) are sentiment signals, not intent — keeping them here made
        # any negative reschedule/follow-up misfire as a complaint.
        Category.COMPLAINT,
        ["not happy", "unacceptable", "terribly", "complaint", "never showed",
         "left damage", "was done terribly", "redo", "filed a complaint"],
    ),
    (Category.CANCELLATION, ["cancel", "call it off", "no longer need"]),
    (
        Category.RESCHEDULE,
        ["reschedule", "move the", "move my", "push my", "push the",
         "different day", "change the time", "move to"],
    ),
    (
        Category.FOLLOW_UP,
        ["following up", "checking in", "status of", "any update", "any news",
         "heard back"],
    ),
    (
        Category.PRICING_QUESTION,
        ["how much", "quote", "your rate", "price", "cost", "estimate"],
    ),
    (
        Category.NEW_REQUEST,
        ["i need help", "looking to book", "can i schedule", "need help with",
         "book", "schedule"],
    ),
]

_URGENT_WORDS = [
    "asap", "as soon as possible", "urgent", "emergency", "today", "right now",
    "right away", "hurry", "couple of hours", "first thing tomorrow",
]
_POSITIVE_WORDS = ["thanks so much", "appreciate", "perfect", "great", "you've been great"]
_NEGATIVE_WORDS = [
    "not happy", "frustrated", "disappointing", "disappointed", "unacceptable",
    "terrible", "terribly", "refund", "never showed", "damage", "angry",
]

_TIMING_RE = re.compile(
    r"\b(today|tomorrow|tonight|this (?:weekend|week|saturday|sunday|morning|afternoon)|"
    r"next (?:week|monday|tuesday|wednesday|thursday|friday)|"
    r"(?:mon|tues|wednes|thurs|fri|satur|sun)day)\b",
    re.IGNORECASE,
)
_PRICE_RE = re.compile(r"\$\s?\d+")


def _homeowner_text(conv: Conversation) -> str:
    """Homeowner turns carry the intent; weight them by using them for category."""
    return " ".join(m.text for m in conv.messages if m.sender.value == "homeowner").lower()


def _full_text(conv: Conversation) -> str:
    return " ".join(m.text for m in conv.messages).lower()


def _detect_category(text: str) -> tuple[Category, int]:
    best: tuple[Category, int] = (Category.NEW_REQUEST, 0)
    for category, signals in _CATEGORY_SIGNALS:
        hits = sum(1 for s in signals if s in text)
        if hits > best[1]:
            best = (category, hits)
    return best


def _detect_service(text: str) -> str | None:
    # Primary signal: the full service label, which a homeowner usually names
    # outright ("I need help with house & apartment cleaning"). Longest label
    # match wins, so "deep / move-out cleaning" beats "house & apartment cleaning".
    best_label_key: str | None = None
    best_label_len = 0
    for svc in load_services():
        label = svc.label.lower()
        if label in text and len(label) > best_label_len:
            best_label_len = len(label)
            best_label_key = svc.key
    if best_label_key is not None:
        return best_label_key

    # Fallback: keyword cues, weighting multiword (more specific) matches higher.
    best_key: str | None = None
    best_score = 0
    for key, keywords in SERVICE_KEYWORDS.items():
        score = sum(len(kw.split()) for kw in keywords if kw in text)
        if score > best_score:
            best_score = score
            best_key = key
    return best_key


def _detect_urgency(text: str) -> Urgency:
    return Urgency.HIGH if any(w in text for w in _URGENT_WORDS) else Urgency.LOW


def _detect_sentiment(text: str) -> Sentiment:
    neg = sum(1 for w in _NEGATIVE_WORDS if w in text)
    pos = sum(1 for w in _POSITIVE_WORDS if w in text)
    if neg > pos:
        return Sentiment.NEGATIVE
    if pos > neg:
        return Sentiment.POSITIVE
    return Sentiment.NEUTRAL


class MockClassifier:
    """Heuristic classifier used in mock mode."""

    mode = "mock"

    def classify(self, conv: Conversation) -> Classification:
        ho_text = _homeowner_text(conv)
        full = _full_text(conv)

        category, hits = _detect_category(ho_text or full)
        service = _detect_service(full)
        urgency = _detect_urgency(full)
        sentiment = _detect_sentiment(full)

        timing_match = _TIMING_RE.search(full)
        price_match = _PRICE_RE.search(full)

        # Confidence reflects signal strength; stays above the routing floor when
        # we have a clear category hit so routing follows the real fields.
        confidence = 0.6 + min(hits, 3) * 0.1
        if service:
            confidence = min(confidence + 0.05, 0.97)

        return Classification(
            category=category,
            entities=Entities(
                service_type=service,
                timing=timing_match.group(0) if timing_match else None,
                urgency=urgency,
                property_ref=None,
                pricing_ref=price_match.group(0) if price_match else None,
            ),
            sentiment=sentiment,
            confidence=round(confidence, 2),
            rationale="heuristic: matched cue words in conversation text",
        )
