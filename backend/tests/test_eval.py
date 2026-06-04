"""The eval gate is the product's quality claim. These tests make a regression
in classification/routing fail CI, not just lower a number quietly."""

from houseaccount.corpus.build import load_corpus, load_golden
from houseaccount.eval.harness import THRESHOLDS, evaluate
from houseaccount.intel.mock import MockClassifier


def test_mock_passes_golden_thresholds():
    report = evaluate(load_golden(), MockClassifier())
    assert report.passed, report.summary()
    assert report.category_f1 >= THRESHOLDS["category_f1"]
    assert report.route_f1 >= THRESHOLDS["route_f1"]
    assert report.entity_score >= THRESHOLDS["entity_score"]
    assert report.sentiment_accuracy >= THRESHOLDS["sentiment_accuracy"]


def test_mock_passes_on_full_corpus_too():
    # Guards against the golden set being accidentally easy.
    report = evaluate(load_corpus(), MockClassifier())
    assert report.passed, report.summary()


def test_golden_set_size():
    assert len(load_golden()) == 25
