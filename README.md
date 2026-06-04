# HouseAccount — Marketplace + Message-Intelligence Engine

Built for **[houseaccount.com](https://www.houseaccount.com/)** ("A better way to
take care of your home"): homeowners get matched with vetted, insured handymen,
and **the platform handles initial communication over text**. This project
targets that exact bottleneck — turning the flood of unstructured **customer chat
conversations** into **actionable insights** — wrapped around a thin trust-first
marketplace.

Two deliverables:

1. **Working software** — a thin marketplace (request → match → quote → booking)
   plus a message-intelligence engine that classifies, extracts, routes, and
   surfaces aggregate insights, wired together (chat → auto-created job).
2. **Diagrams** — [architecture](diagrams/architecture.md) and
   [capability](diagrams/capability.md) (Mermaid; render in VS Code / GitHub).

Scope, trade-offs, and the success bar are recorded in [DECISIONS.md](DECISIONS.md).
The research-backed PRD is [houseaccount_requirements_document.md](houseaccount_requirements_document.md).

## What it does

- **Classifies** each customer chat into one of six intents (new request,
  reschedule, cancellation, complaint, pricing question, follow-up).
- **Extracts** service type, timing, pricing reference, urgency, and sentiment.
- **Routes deterministically** — low-risk intents are automated (e.g. a new
  request auto-creates a marketplace job); complaints, cancellations, negative
  sentiment, high urgency, or low confidence are **held for human review** with a
  stated reason. The model does judgment; explicit code does orchestration.
- **Aggregates** everything into an ops dashboard: volume by category, sentiment,
  routing split, top services, complaint & human-review rates.

## Quality is measured, not asserted

The engine is gated by an offline eval over a hand-verified **golden set (25
conversations)**. Current mock-mode results:

| Metric | Threshold | Golden | Full corpus (120) |
|--------|-----------|--------|-------------------|
| category F1 | ≥ 0.85 | **0.92** | 0.87 |
| route / escalation F1 | ≥ 0.90 | **1.00** | 0.98 |
| entity score | ≥ 0.80 | **1.00** | 1.00 |
| sentiment accuracy | ≥ 0.80 | **1.00** | 1.00 |

The mock classifier reads only message text (never the labels), so the eval is
honest; the live Claude Opus path is expected to meet or exceed it.

## Run it

### Backend (Python 3.12+)

```bash
cd backend
python -m venv ../.venv
../.venv/Scripts/python.exe -m pip install -e ".[dev]"   # Windows; use ../.venv/bin/python on macOS/Linux
../.venv/Scripts/python.exe -m houseaccount.cli gen       # build corpus + golden set
../.venv/Scripts/python.exe -m houseaccount.cli eval      # run the eval gate (mock)
../.venv/Scripts/python.exe -m uvicorn houseaccount.api.app:app --port 8077
```

Live mode (Claude Opus 4.8): set `ANTHROPIC_API_KEY` and `HA_MODE=live`
(in the environment or a `.env` file). Default is `mock` — fully offline.

### Frontend (Node 18+)

```bash
cd frontend
pnpm install
pnpm dev        # http://localhost:5173 (proxies /api to :8000)
```

## Test / lint / typecheck

```bash
# backend
cd backend && ../.venv/Scripts/python.exe -m pytest        # 26 tests
../.venv/Scripts/python.exe -m ruff check .
../.venv/Scripts/python.exe -m mypy houseaccount
# frontend
cd frontend && pnpm test                                   # 9 tests
pnpm build
```

## Layout

```text
backend/houseaccount/
  corpus/      synthetic chat generator + TaskRabbit taxonomy (scraped, grounded)
  intel/       engine: classifier (mock + Opus), deterministic router
  marketplace/ providers, matching, quotes, bookings, engine write-backs
  eval/        metrics + threshold-gated harness
  api/         FastAPI app
frontend/src/
  components/  InsightsConsole · ConversationDrawer · Marketplace
diagrams/      architecture.md · capability.md
```

## Notes

- **Data:** chat text is synthetic and seeded (reproducible). Only TaskRabbit's
  public *category list* was fetched (saved in
  `backend/houseaccount/data/taskrabbit_categories_raw.txt`); a committed fallback
  keeps the build offline-reproducible.
- **Model choice:** Opus 4.8 on the live path for edge-case accuracy. At real
  message volume, drop to Sonnet — see DECISIONS.md.
