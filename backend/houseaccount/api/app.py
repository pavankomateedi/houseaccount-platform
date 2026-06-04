"""FastAPI app: marketplace + message-intelligence endpoints.

Insights are computed once over the corpus (lazily, in the active mode) and
cached in app state, since the corpus is static for a demo run.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from ..config import get_mode
from ..corpus.build import load_corpus, load_golden
from ..corpus.reviews import sort_reviews
from ..eval.harness import EvalReport, evaluate
from ..insights_report import AggregateStats, InsightView, aggregate, compute_views
from ..intel.engine import get_classifier
from ..marketplace import service
from ..marketplace.models import Booking, Provider, Quote, Review, ServiceRequest
from ..marketplace.store import store
from ..taxonomy import load_services

app = FastAPI(title="HouseAccount API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@lru_cache(maxsize=1)
def _views() -> list[InsightView]:
    return compute_views(load_corpus(), get_classifier())


def _find_view(conversation_id: str) -> InsightView:
    for v in _views():
        if v.conversation.id == conversation_id:
            return v
    raise HTTPException(status_code=404, detail=f"conversation {conversation_id} not found")


# --- meta ----------------------------------------------------------------

@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "mode": get_mode()}


@app.get("/api/taxonomy")
def taxonomy() -> list[dict[str, str]]:
    return [{"key": s.key, "label": s.label, "group": s.group} for s in load_services()]


# --- insights ------------------------------------------------------------

@app.get("/api/insights")
def insights() -> list[InsightView]:
    return _views()


@app.get("/api/insights/stats")
def insights_stats() -> AggregateStats:
    return aggregate(_views())


@app.get("/api/insights/{conversation_id}")
def insight_detail(conversation_id: str) -> InsightView:
    return _find_view(conversation_id)


class ApplyResult(BaseModel):
    created_request_id: str | None
    request: ServiceRequest | None
    message: str


@app.post("/api/insights/{conversation_id}/apply")
def apply_insight(conversation_id: str) -> ApplyResult:
    view = _find_view(conversation_id)
    req_id = service.apply_insight(
        store,
        view.insight,
        homeowner_id=view.conversation.homeowner_id,
        zip_code=view.conversation.zip_code,
    )
    if req_id is None:
        return ApplyResult(
            created_request_id=None,
            request=None,
            message="No auto-action: routed to human review or not a job-creating intent.",
        )
    return ApplyResult(
        created_request_id=req_id,
        request=store.requests[req_id],
        message="Service request auto-created from chat.",
    )


# --- eval (handy for the demo) -------------------------------------------

@app.get("/api/eval")
def run_eval(mode: str | None = None) -> EvalReport:
    return evaluate(load_golden(), get_classifier(mode))


# --- marketplace ---------------------------------------------------------

@app.get("/api/providers")
def providers() -> list[Provider]:
    return list(store.providers.values())


@app.get("/api/requests")
def requests() -> list[ServiceRequest]:
    return list(store.requests.values())


class CreateRequest(BaseModel):
    homeowner_id: str
    service_type: str
    zip_code: str
    timing: str | None = None
    notes: str = ""


@app.post("/api/requests")
def create_request(body: CreateRequest) -> ServiceRequest:
    return service.create_request(
        store,
        homeowner_id=body.homeowner_id,
        service_type=body.service_type,
        zip_code=body.zip_code,
        timing=body.timing,
        notes=body.notes,
    )


@app.post("/api/requests/{request_id}/quotes")
def make_quotes(request_id: str) -> list[Quote]:
    if request_id not in store.requests:
        raise HTTPException(status_code=404, detail="request not found")
    return service.generate_quotes(store, request_id)


@app.get("/api/quotes")
def quotes(request_id: str | None = None) -> list[Quote]:
    items = list(store.quotes.values())
    if request_id:
        items = [q for q in items if q.request_id == request_id]
    return items


class AcceptBody(BaseModel):
    scheduled_time: str | None = None


@app.post("/api/quotes/{quote_id}/accept")
def accept(quote_id: str, body: AcceptBody) -> Booking:
    if quote_id not in store.quotes:
        raise HTTPException(status_code=404, detail="quote not found")
    return service.accept_quote(store, quote_id, body.scheduled_time)


@app.get("/api/bookings")
def bookings() -> list[Booking]:
    return list(store.bookings.values())


@app.get("/api/reviews")
def reviews() -> list[Review]:
    # Sorted positive → neutral → negative (highest ratings first within each).
    return sort_reviews(list(store.reviews.values()))


# --- static frontend (production single-service) --------------------------
# In production the built React app is served from the same origin as the API,
# so there is no CORS or dev-proxy involved. Mounted last so /api/* wins.
# Skipped automatically in dev/tests when no build exists.
def _frontend_dist() -> Path | None:
    env = os.getenv("HA_STATIC_DIR")
    candidates = [Path(env)] if env else []
    candidates.append(Path(__file__).resolve().parents[3] / "frontend" / "dist")
    for c in candidates:
        if c.is_dir() and (c / "index.html").exists():
            return c
    return None


_dist = _frontend_dist()
if _dist is not None:
    app.mount("/", StaticFiles(directory=str(_dist), html=True), name="spa")
