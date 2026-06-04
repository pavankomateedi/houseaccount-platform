"""Synthetic reviews must be reproducible, mostly positive, and correctly sorted."""

from houseaccount.corpus.reviews import generate_reviews, sort_reviews
from houseaccount.marketplace.store import MarketplaceStore
from houseaccount.models import Sentiment


def _providers():
    return list(MarketplaceStore().providers.values())


def test_generation_is_deterministic():
    a = generate_reviews(_providers(), seed=42)
    b = generate_reviews(_providers(), seed=42)
    assert [r.model_dump() for r in a] == [r.model_dump() for r in b]


def test_corpus_skews_positive():
    reviews = generate_reviews(_providers(), seed=42)
    positive = sum(1 for r in reviews if r.sentiment is Sentiment.POSITIVE)
    assert positive / len(reviews) > 0.5  # "mostly positive"


def test_ratings_track_sentiment():
    for r in generate_reviews(_providers(), seed=42):
        if r.sentiment is Sentiment.POSITIVE:
            assert r.rating >= 4
        elif r.sentiment is Sentiment.NEUTRAL:
            assert r.rating == 3
        else:
            assert r.rating <= 2


def test_sort_puts_positive_first_negative_last():
    ordered = sort_reviews(generate_reviews(_providers(), seed=42))
    ranks = {Sentiment.POSITIVE: 0, Sentiment.NEUTRAL: 1, Sentiment.NEGATIVE: 2}
    seq = [ranks[r.sentiment] for r in ordered]
    assert seq == sorted(seq)  # non-decreasing: positives, then neutral, then negative
    # within positives, higher ratings first
    pos = [r.rating for r in ordered if r.sentiment is Sentiment.POSITIVE]
    assert pos == sorted(pos, reverse=True)
