"""Runtime configuration.

The engine runs in one of two modes:
  - ``mock``  : deterministic heuristic classifier, no network. Used by tests,
                the eval harness, and CI. The default.
  - ``live``  : calls Claude Opus 4.8. Requires ANTHROPIC_API_KEY.

Mode is read from the ``HA_MODE`` env var so the same code path serves both.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PACKAGE_DIR = Path(__file__).resolve().parent
DATA_DIR = PACKAGE_DIR / "data"

# Live model. Sonnet would be the volume choice; Opus picked for edge-case accuracy.
LIVE_MODEL = "claude-opus-4-8"

# Deterministic seed for corpus generation — reproducible across machines.
CORPUS_SEED = 20260603
CORPUS_SIZE = 120
GOLDEN_SIZE = 25


def get_mode() -> str:
    """Return 'mock' or 'live'. Defaults to mock so nothing needs an API key."""
    mode = os.getenv("HA_MODE", "mock").strip().lower()
    return "live" if mode == "live" else "mock"


def get_api_key() -> str | None:
    return os.getenv("ANTHROPIC_API_KEY")
