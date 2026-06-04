"""In-memory marketplace store with a deterministic seed of vetted providers.

In-memory is intentional for a one-week build; the service layer is written so a
real datastore could replace this without touching callers.
"""

from __future__ import annotations

from .models import Booking, Provider, Quote, Review, ServiceRequest

_REVIEW_SEED = 20260603

# Deterministic provider seed. Coverage zips match the corpus generator's zips so
# chat-driven requests always find eligible pros.
_SEED_PROVIDERS: list[Provider] = [
    Provider(id="pro-01", name="Bayview Handy Co.",
             services=["handyman", "furniture_assembly", "tv_mounting", "smart_home"],
             coverage_zips=["94110", "94114", "94131"], rating=4.8, jobs_done=312),
    Provider(id="pro-02", name="Mission Plumb & Drain",
             services=["plumbing", "appliance_repair", "handyman"],
             coverage_zips=["94110", "94103", "94112"], rating=4.6, jobs_done=205),
    Provider(id="pro-03", name="Sunset Sparkle Cleaning",
             services=["house_cleaning", "deep_cleaning"],
             coverage_zips=["94114", "94117", "94131"], rating=4.9, jobs_done=540),
    Provider(id="pro-04", name="Golden Gate Movers",
             services=["help_moving", "heavy_lifting", "junk_removal"],
             coverage_zips=["94103", "94110", "94112"], rating=4.4, jobs_done=178),
    Provider(id="pro-05", name="BrightSpark Electric",
             services=["electrical", "smart_home", "appliance_repair"],
             coverage_zips=["94117", "94114", "94103"], rating=4.7, jobs_done=261),
    Provider(id="pro-06", name="Fresh Coat Painting",
             services=["painting", "handyman"],
             coverage_zips=["94110", "94112", "94131"], rating=4.5, jobs_done=143),
    Provider(id="pro-07", name="GreenThumb Yard Care",
             services=["yard_work", "junk_removal"],
             coverage_zips=["94117", "94131", "94112"], rating=4.3, jobs_done=98),
    Provider(id="pro-08", name="AllFix Home Services",
             services=["handyman", "plumbing", "electrical", "appliance_repair",
                       "furniture_assembly", "tv_mounting"],
             coverage_zips=["94110", "94114", "94103", "94117", "94112", "94131"],
             rating=4.2, jobs_done=421),
]


class MarketplaceStore:
    """Holds marketplace state. One instance per process; resettable for tests."""

    def __init__(self) -> None:
        self.providers: dict[str, Provider] = {}
        self.requests: dict[str, ServiceRequest] = {}
        self.quotes: dict[str, Quote] = {}
        self.bookings: dict[str, Booking] = {}
        self.reviews: dict[str, Review] = {}
        self._counter = 0
        self.seed()

    def seed(self) -> None:
        # Imported here to avoid an import cycle (corpus.reviews → marketplace.models).
        from ..corpus.reviews import generate_reviews

        self.providers = {p.id: p.model_copy(deep=True) for p in _SEED_PROVIDERS}
        self.requests.clear()
        self.quotes.clear()
        self.bookings.clear()
        reviews = generate_reviews(list(self.providers.values()), seed=_REVIEW_SEED, per_provider=8)
        self.reviews = {r.id: r for r in reviews}
        self._counter = 0

    def next_id(self, prefix: str) -> str:
        self._counter += 1
        return f"{prefix}-{self._counter:04d}"


# Process-wide store used by the API. Tests construct their own.
store = MarketplaceStore()
