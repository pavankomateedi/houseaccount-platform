"""Metro markets for the synthetic dataset.

The development data is concentrated in three real metros with realistic ZIP
prefixes and a market cost index (SF Bay and NYC run pricier than Dallas). The
cost index is applied to the baseline estimate, so geography is already priced in
and the model's learnable signal stays the scope in the job description.

Used by data/make_synthetic.py (to generate rows) and eval/export_ui.py (to show
the market breakdown). Pure + importable + tested.
"""

from __future__ import annotations

from dataclasses import dataclass
from random import Random


@dataclass(frozen=True)
class Market:
    name: str
    prefixes: tuple[str, ...]  # 3-digit ZIP prefixes (for classifying any ZIP)
    zips: tuple[str, ...]  # the 1-2 serviced ZIPs in this market
    cost_index: float
    weight: int


MARKETS: tuple[Market, ...] = (
    Market("New York, NY", ("100", "101", "102", "103", "104", "112", "113"),
           ("10023", "11201"), 1.35, 4),
    Market("Dallas, TX", ("750", "751", "752"),
           ("75201", "75007"), 0.92, 4),
    Market("SF Bay Area, CA", ("941", "945", "950"),
           ("94105", "95014"), 1.45, 3),
)


def market_for_zip(zip_code: object) -> str | None:
    """Market name for a ZIP, or None if it is outside the seeded metros."""
    prefix = str(zip_code)[:3]
    for market in MARKETS:
        if prefix in market.prefixes:
            return market.name
    return None


def weighted_market(rng: Random) -> Market:
    return rng.choices(MARKETS, weights=[m.weight for m in MARKETS], k=1)[0]


def sample_zip(market: Market, rng: Random) -> str:
    """One of the market's serviced ZIPs."""
    return rng.choice(market.zips)
