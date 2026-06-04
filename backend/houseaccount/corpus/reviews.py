"""Seeded synthetic provider reviews.

Mostly positive, with a neutral and negative tail — realistic for a vetted
marketplace. Deterministic for a given seed. Ratings track sentiment
(positive 4-5, neutral 3, negative 1-2).
"""

from __future__ import annotations

import random

from ..marketplace.models import Provider, Review
from ..models import Sentiment
from ..taxonomy import label_for

# Review sentiment mix: 60% positive, 30% neutral, 10% negative (per request).
# Exact-count allocation, so the displayed split matches; headline avg ~4.0★.
_SENTIMENT_MIX: list[tuple[Sentiment, float]] = [
    (Sentiment.POSITIVE, 0.60),
    (Sentiment.NEUTRAL, 0.30),
    (Sentiment.NEGATIVE, 0.10),
]

_TEXT: dict[Sentiment, list[str]] = {
    Sentiment.POSITIVE: [
        "Fantastic {svc} work — punctual, tidy, and fairly priced. Highly recommend!",
        "{name} did an amazing job. Communication was great and the result is perfect.",
        "Booked through HouseAccount and couldn't be happier. Will use {name} again.",
        "Showed up on time, finished early, and cleaned up afterward. Five stars.",
        "Exactly the pro I needed for {svc}. Professional and friendly throughout.",
    ],
    Sentiment.NEUTRAL: [
        "Decent {svc} job. Got it done, nothing remarkable either way.",
        "Service was okay — showed up a little late but finished the work.",
        "Fair price and acceptable quality. Would consider {name} again.",
        "It was fine. The {svc} works, though communication could be tighter.",
    ],
    Sentiment.NEGATIVE: [
        "Disappointed with the {svc} — had to call them back to redo part of it.",
        "Ran late and the quote crept up at the end. Not thrilled.",
        "Quality was below what I expected for {svc}. Wouldn't rebook {name}.",
        "Hard to reach after booking and the work felt rushed.",
    ],
}

_SENTIMENT_RANK = {Sentiment.POSITIVE: 0, Sentiment.NEUTRAL: 1, Sentiment.NEGATIVE: 2}


def _rating(rng: random.Random, sentiment: Sentiment) -> int:
    """Ratings track sentiment; positives skew to 5 so the average lands 4.5★+."""
    if sentiment is Sentiment.POSITIVE:
        return rng.choices([5, 4], weights=[0.85, 0.15], k=1)[0]
    if sentiment is Sentiment.NEUTRAL:
        return 3
    return rng.choices([2, 1], weights=[0.6, 0.4], k=1)[0]


def _sentiment_sequence(total: int) -> list[Sentiment]:
    """Exact-count sentiment list matching _SENTIMENT_MIX proportions.

    Using exact counts (not random draws) so the displayed split lands on the
    requested 60% / 30% / 10% rather than drifting with sampling noise.
    """
    neutral = round(total * dict(_SENTIMENT_MIX)[Sentiment.NEUTRAL])
    negative = round(total * dict(_SENTIMENT_MIX)[Sentiment.NEGATIVE])
    positive = total - neutral - negative
    return (
        [Sentiment.POSITIVE] * positive
        + [Sentiment.NEUTRAL] * neutral
        + [Sentiment.NEGATIVE] * negative
    )


def generate_reviews(providers: list[Provider], seed: int, per_provider: int = 4) -> list[Review]:
    rng = random.Random(seed)
    total = len(providers) * per_provider
    sequence = _sentiment_sequence(total)
    rng.shuffle(sequence)
    reviews: list[Review] = []
    for n, sentiment in enumerate(sequence, start=1):
        provider = providers[(n - 1) % len(providers)]
        service = rng.choice(provider.services)
        reviews.append(
            Review(
                id=f"rev-{n:04d}",
                provider_id=provider.id,
                homeowner_id=f"ho-{rng.randint(1000, 9999)}",
                service_type=service,
                rating=_rating(rng, sentiment),
                sentiment=sentiment,
                text=rng.choice(_TEXT[sentiment]).format(
                    svc=label_for(service).lower(), name=provider.name
                ),
            )
        )
    return reviews


def sort_reviews(reviews: list[Review]) -> list[Review]:
    """Positive first, then neutral, then negative; higher ratings first within."""
    return sorted(reviews, key=lambda r: (_SENTIMENT_RANK[r.sentiment], -r.rating))
