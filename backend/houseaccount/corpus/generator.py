"""Seeded synthetic chat-conversation generator.

Produces multi-turn conversations between a homeowner and a provider/agent, each
carrying baked-in ground-truth labels. Output is deterministic for a given seed,
so the corpus and golden set are reproducible across machines.

Design contract that keeps the eval honest:
  - Messages are woven from natural-language fragments that carry the same
    real-world cues a heuristic or LLM keys off (service labels, urgency words,
    sentiment words, intent phrases).
  - The mock classifier reads ONLY the message text, never the ground truth.
  - Ground-truth ``route`` is computed by the SAME deterministic rule the engine
    uses, applied to the true fields, so route F1 measures field recovery.
  - Ground-truth ``timing``/``pricing_ref`` record what was actually woven into
    the text (or None), so entity scoring rewards correct silence.
"""

from __future__ import annotations

import random
from collections.abc import Sequence

from ..intel.router import decide_route
from ..marketplace.store import _SEED_PROVIDERS
from ..models import (
    Category,
    Conversation,
    GroundTruth,
    Message,
    Sender,
    Sentiment,
    Urgency,
)
from ..taxonomy import label_for, service_keys

# --- fragment pools -------------------------------------------------------

_TIMING_NORMAL = [
    "this Saturday morning",
    "next Monday",
    "Thursday afternoon",
    "next Tuesday",
    "this Sunday",
]
# Urgent timings deliberately contain a detectable day/time word.
_TIMING_URGENT = [
    "today if at all possible",
    "first thing tomorrow",
    "later today",
    "by tonight",
]
_PROPERTY = [
    "my 2-bedroom apartment",
    "our townhouse",
    "a small studio",
    "my 3-bed house",
    "the upstairs unit",
    "our condo downtown",
]
_PRICE = ["$120", "around $200", "the $85 quote", "$300 estimate", "$150"]
_ZIPS = ["94110", "94114", "94103", "94117", "94112", "94131"]

# Openers that name the service. ``{timing}`` only where a homeowner would
# naturally state it (booking / reschedule); other intents omit it on purpose.
_OPENERS: dict[Category, list[str]] = {
    Category.NEW_REQUEST: [
        "Hi, I need help with {svc} at {prop}.",
        "Looking to book {svc} — can someone come {timing}?",
        "Can I schedule {svc}? I'd like it done {timing}.",
    ],
    Category.RESCHEDULE: [
        "I need to reschedule my {svc} appointment to {timing}.",
        "Can we move the {svc} booking to {timing} instead?",
        "Something came up — please push my {svc} visit to {timing}.",
    ],
    Category.CANCELLATION: [
        "I'd like to cancel my {svc} booking, I no longer need it.",
        "Please cancel the {svc} appointment — call it off for now.",
        "I have to cancel my upcoming {svc} service.",
    ],
    Category.COMPLAINT: [
        "I'm really not happy — the {svc} job was done terribly.",
        "This is unacceptable. The provider for my {svc} never showed up.",
        "I want to file a complaint about the {svc} service, it left damage.",
    ],
    Category.PRICING_QUESTION: [
        "How much would {svc} cost for {prop}?",
        "Can I get a quote for {svc}? What's your rate?",
        "What's the price estimate for {svc}?",
    ],
    Category.FOLLOW_UP: [
        "Just following up on my {svc} request — any update?",
        "Checking in on the status of my {svc} booking.",
        "Haven't heard back about the {svc} job, any news?",
    ],
}

_PROVIDER_REPLIES = [
    "Thanks for reaching out! Let me look into that for you.",
    "Happy to help — give me one moment.",
    "Got it, checking the schedule now.",
    "Understood. Let me pull up your details.",
]

# Sentiment-free filler. The ``{price}`` variant is the only place pricing is
# woven, so ground-truth pricing presence tracks whether it was chosen.
_FILLER_PLAIN = [
    "It's {prop}, by the way.",
    "Please share the next steps.",
    "Let me know what you need from me.",
]
_FILLER_PRICE = "I was quoted {price} earlier, if that helps."

_CLOSERS: dict[Sentiment, list[str]] = {
    Sentiment.POSITIVE: [
        "Thanks so much, you've been great!",
        "Perfect, I really appreciate the help.",
    ],
    Sentiment.NEUTRAL: [
        "Okay, let me know.",
        "Sounds good.",
    ],
    Sentiment.NEGATIVE: [
        "Honestly I'm very frustrated and want this resolved.",
        "This is really disappointing — I expect a refund.",
    ],
}

_URGENT_TAIL = [
    "This is urgent.",
    "I really need this handled quickly.",
    "It's an emergency, please hurry.",
]

# Skewed positive overall (a healthy marketplace): positive > neutral > negative.
# Complaints stay uniformly negative, but they're a small slice of the corpus.
_SENTIMENT_WEIGHTS: dict[Category, list[tuple[Sentiment, float]]] = {
    Category.NEW_REQUEST: [(Sentiment.POSITIVE, 0.7), (Sentiment.NEUTRAL, 0.3)],
    Category.RESCHEDULE: [
        (Sentiment.POSITIVE, 0.5), (Sentiment.NEUTRAL, 0.45), (Sentiment.NEGATIVE, 0.05),
    ],
    Category.CANCELLATION: [
        (Sentiment.NEUTRAL, 0.6), (Sentiment.NEGATIVE, 0.3), (Sentiment.POSITIVE, 0.1),
    ],
    Category.COMPLAINT: [(Sentiment.NEGATIVE, 1.0)],
    Category.PRICING_QUESTION: [(Sentiment.POSITIVE, 0.7), (Sentiment.NEUTRAL, 0.3)],
    Category.FOLLOW_UP: [
        (Sentiment.POSITIVE, 0.5), (Sentiment.NEUTRAL, 0.35), (Sentiment.NEGATIVE, 0.15),
    ],
}

# Category mix for the corpus. Complaints are deliberately rare (<10%).
_CATEGORY_DISTRIBUTION: list[tuple[Category, float]] = [
    (Category.NEW_REQUEST, 0.26),
    (Category.PRICING_QUESTION, 0.20),
    (Category.FOLLOW_UP, 0.18),
    (Category.RESCHEDULE, 0.15),
    (Category.CANCELLATION, 0.15),
    (Category.COMPLAINT, 0.06),
]

# Urgency is low/high only — "medium" is genuinely indistinguishable from "low"
# in short chat text, so we don't pretend to label it. The enum keeps MEDIUM for
# the live model / UI.
_URGENCY_WEIGHTS: dict[Category, list[tuple[Urgency, float]]] = {
    Category.NEW_REQUEST: [(Urgency.LOW, 0.7), (Urgency.HIGH, 0.3)],
    Category.RESCHEDULE: [(Urgency.LOW, 0.9), (Urgency.HIGH, 0.1)],
    Category.CANCELLATION: [(Urgency.LOW, 1.0)],
    Category.COMPLAINT: [(Urgency.LOW, 0.4), (Urgency.HIGH, 0.6)],
    Category.PRICING_QUESTION: [(Urgency.LOW, 1.0)],
    Category.FOLLOW_UP: [(Urgency.LOW, 0.7), (Urgency.HIGH, 0.3)],
}


def _weighted(rng: random.Random, choices: Sequence[tuple[object, float]]) -> object:
    population = [c[0] for c in choices]
    weights = [c[1] for c in choices]
    return rng.choices(population, weights=weights, k=1)[0]


def _pick_provider(rng: random.Random, service_type: str, zip_code: str):  # type: ignore[no-untyped-def]
    """Attribute the chat to a real provider that fits, so each thread is a
    concrete homeowner ↔ provider conversation."""
    serving = [
        p for p in _SEED_PROVIDERS if service_type in p.services and zip_code in p.coverage_zips
    ]
    if not serving:
        serving = [p for p in _SEED_PROVIDERS if service_type in p.services]
    if not serving:
        serving = list(_SEED_PROVIDERS)
    return rng.choice(serving)


def _build_conversation(rng: random.Random, idx: int, category: Category) -> Conversation:
    service_type = rng.choice(service_keys())
    svc_label = label_for(service_type).lower()
    urgency: Urgency = _weighted(rng, _URGENCY_WEIGHTS[category])  # type: ignore[assignment]
    sentiment: Sentiment = _weighted(rng, _SENTIMENT_WEIGHTS[category])  # type: ignore[assignment]
    prop = rng.choice(_PROPERTY)

    opener_tmpl = rng.choice(_OPENERS[category])
    has_timing_slot = "{timing}" in opener_tmpl
    timing = rng.choice(_TIMING_URGENT if urgency is Urgency.HIGH else _TIMING_NORMAL)
    woven_timing = timing if has_timing_slot else None

    opener = opener_tmpl.format(svc=svc_label, prop=prop, timing=timing)
    if urgency is Urgency.HIGH:
        opener = f"{opener} {rng.choice(_URGENT_TAIL)}"

    msgs: list[Message] = [
        Message(sender=Sender.HOMEOWNER, text=opener),
        Message(sender=Sender.PROVIDER, text=rng.choice(_PROVIDER_REPLIES)),
    ]

    # Optional pricing filler — recorded in ground truth when used.
    woven_price: str | None = None
    if rng.random() < 0.5:
        woven_price = rng.choice(_PRICE)
        msgs.append(
            Message(sender=Sender.HOMEOWNER, text=_FILLER_PRICE.format(price=woven_price))
        )

    for _ in range(rng.randint(1, 2)):
        msgs.append(
            Message(sender=Sender.HOMEOWNER, text=rng.choice(_FILLER_PLAIN).format(prop=prop))
        )
        if rng.random() < 0.6:
            msgs.append(Message(sender=Sender.PROVIDER, text=rng.choice(_PROVIDER_REPLIES)))

    msgs.append(Message(sender=Sender.HOMEOWNER, text=rng.choice(_CLOSERS[sentiment])))

    zip_code = rng.choice(_ZIPS)
    provider = _pick_provider(rng, service_type, zip_code)
    route, _reason = decide_route(category, urgency, sentiment, confidence=1.0)
    return Conversation(
        id=f"conv-{idx:04d}",
        homeowner_id=f"ho-{rng.randint(1000, 9999)}",
        zip_code=zip_code,
        messages=msgs,
        provider_id=provider.id,
        provider_name=provider.name,
        ground_truth=GroundTruth(
            category=category,
            service_type=service_type,
            timing=woven_timing,
            pricing_ref=woven_price,
            urgency=urgency,
            sentiment=sentiment,
            route=route,
        ),
    )


def generate_corpus(size: int, seed: int) -> list[Conversation]:
    """Generate ``size`` conversations using the weighted category mix.

    Complaints are intentionally rare (see ``_CATEGORY_DISTRIBUTION``), reflecting
    a healthy marketplace where most chats are requests, pricing, and follow-ups.
    """
    rng = random.Random(seed)
    cats = [c for c, _ in _CATEGORY_DISTRIBUTION]
    weights = [w for _, w in _CATEGORY_DISTRIBUTION]
    convos: list[Conversation] = []
    for i in range(size):
        category = rng.choices(cats, weights=weights, k=1)[0]
        convos.append(_build_conversation(rng, i, category))
    rng.shuffle(convos)
    return convos
