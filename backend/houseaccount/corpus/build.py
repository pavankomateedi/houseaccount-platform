"""Build + persist the corpus and the stratified golden set.

The golden set is a deterministic, category-stratified subset of the corpus.
Because generation is seeded and labels are correct by construction, the golden
set is reproducible; it is the hand-verifiable slice the eval gates against.
"""

from __future__ import annotations

import json
from pathlib import Path

from ..config import CORPUS_SEED, CORPUS_SIZE, DATA_DIR, GOLDEN_SIZE
from ..models import Category, Conversation
from .generator import generate_corpus

CORPUS_PATH = DATA_DIR / "corpus.json"
GOLDEN_PATH = DATA_DIR / "golden.json"


def select_golden(corpus: list[Conversation], size: int) -> list[Conversation]:
    """Pick an even slice across categories, deterministically."""
    per_category = max(1, size // len(Category))
    chosen: list[Conversation] = []
    for category in Category:
        in_cat = [c for c in corpus if c.ground_truth and c.ground_truth.category == category]
        chosen.extend(in_cat[:per_category])
    # Top up to exactly `size` from whatever remains, preserving order.
    if len(chosen) < size:
        chosen_ids = {c.id for c in chosen}
        for c in corpus:
            if c.id not in chosen_ids:
                chosen.append(c)
                if len(chosen) == size:
                    break
    return chosen[:size]


def _dump(path: Path, convs: list[Conversation]) -> None:
    payload = [c.model_dump(mode="json") for c in convs]
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _load(path: Path) -> list[Conversation]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return [Conversation.model_validate(item) for item in raw]


def build_and_save() -> tuple[int, int]:
    corpus = generate_corpus(CORPUS_SIZE, CORPUS_SEED)
    golden = select_golden(corpus, GOLDEN_SIZE)
    _dump(CORPUS_PATH, corpus)
    _dump(GOLDEN_PATH, golden)
    return len(corpus), len(golden)


def load_corpus() -> list[Conversation]:
    if not CORPUS_PATH.exists():
        build_and_save()
    return _load(CORPUS_PATH)


def load_golden() -> list[Conversation]:
    if not GOLDEN_PATH.exists():
        build_and_save()
    return _load(GOLDEN_PATH)
