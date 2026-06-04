"""The corpus must be deterministic and internally consistent, or the eval lies."""

from houseaccount.corpus.generator import generate_corpus
from houseaccount.intel.router import decide_route
from houseaccount.taxonomy import service_keys


def test_generation_is_deterministic():
    a = generate_corpus(40, seed=123)
    b = generate_corpus(40, seed=123)
    assert [c.model_dump() for c in a] == [c.model_dump() for c in b]


def test_different_seed_changes_corpus():
    a = generate_corpus(40, seed=1)
    b = generate_corpus(40, seed=2)
    # Same id set (positional ids), but different content/ordering.
    assert {c.id for c in a} == {c.id for c in b}
    assert [c.model_dump() for c in a] != [c.model_dump() for c in b]


def test_every_conversation_is_labeled_and_multi_turn():
    for conv in generate_corpus(60, seed=7):
        assert conv.ground_truth is not None
        assert len(conv.messages) >= 3  # multi-turn, not single message


def test_ground_truth_route_matches_router():
    # GT route must equal the deterministic rule applied to GT fields.
    for conv in generate_corpus(60, seed=7):
        gt = conv.ground_truth
        assert gt is not None
        expected, _ = decide_route(gt.category, gt.urgency, gt.sentiment, confidence=1.0)
        assert gt.route is expected


def test_woven_entities_are_present_in_text():
    # If GT claims a timing/pricing, the text must actually contain it.
    for conv in generate_corpus(60, seed=7):
        gt = conv.ground_truth
        assert gt is not None
        text = " ".join(m.text for m in conv.messages)
        if gt.pricing_ref:
            assert gt.pricing_ref in text
        if gt.timing:
            assert gt.timing in text
        assert gt.service_type in service_keys()
