"""Service taxonomy access + keyword signals.

The taxonomy is the public TaskRabbit-style category list (see
``corpus/taxonomy_scrape.py`` for how it is sourced). Everything else in the
build treats it as the authoritative set of service types.
"""

from __future__ import annotations

import functools
import json

from .config import DATA_DIR


class Service:
    __slots__ = ("key", "label", "group")

    def __init__(self, key: str, label: str, group: str) -> None:
        self.key = key
        self.label = label
        self.group = group


@functools.lru_cache(maxsize=1)
def load_services() -> list[Service]:
    raw = json.loads((DATA_DIR / "taxonomy.json").read_text(encoding="utf-8"))
    return [Service(s["key"], s["label"], s["group"]) for s in raw["services"]]


@functools.lru_cache(maxsize=1)
def service_keys() -> tuple[str, ...]:
    return tuple(s.key for s in load_services())


def label_for(key: str) -> str:
    for s in load_services():
        if s.key == key:
            return s.label
    return key


# Keyword signals per service type. Used by the synthetic generator (to weave
# natural language) and by the mock classifier (to detect service from text).
# Real messages contain exactly these kinds of cues, so a heuristic that keys
# off them is a fair, text-only baseline — it never reads the ground-truth label.
SERVICE_KEYWORDS: dict[str, list[str]] = {
    "house_cleaning": ["clean", "cleaning", "tidy", "vacuum", "dusting"],
    "deep_cleaning": ["deep clean", "move-out clean", "move out clean", "scrub"],
    "furniture_assembly": ["assemble", "assembly", "ikea", "flat-pack", "put together"],
    "tv_mounting": ["mount", "mounting", "tv on the wall", "hang the tv", "wall mount"],
    "help_moving": ["move", "moving", "relocate", "boxes", "movers"],
    "heavy_lifting": ["heavy lifting", "carry", "load", "couch upstairs", "lift"],
    "junk_removal": ["junk", "haul away", "trash removal", "dispose", "old mattress"],
    "handyman": ["handyman", "fix", "repair", "odd jobs", "patch", "door won't"],
    "plumbing": ["plumb", "leak", "faucet", "drain", "toilet", "pipe"],
    "electrical": ["electric", "outlet", "wiring", "light fixture", "breaker"],
    "appliance_repair": ["appliance", "dishwasher", "washer", "dryer", "fridge", "oven"],
    "painting": ["paint", "painting", "repaint", "primer", "wall color"],
    "yard_work": ["yard", "lawn", "mow", "weeds", "garden", "leaves"],
    "smart_home": ["smart home", "thermostat", "nest", "smart lock", "doorbell camera"],
}
