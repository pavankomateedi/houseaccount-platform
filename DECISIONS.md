# HouseAccount — Locked Decisions (Week 6)

Decisions reached via a structured grill-me interrogation on 2026-06-03.
Foundation: [houseaccount_requirements_document.md](houseaccount_requirements_document.md)
(research-backed PRD). These decisions scope what is actually built this week.

## Deliverables

1. **Working code** — a thin marketplace **plus** a message-intelligence engine,
   both running and demoed.
2. **Platform "proposal" = two diagrams only** — an architecture diagram and a
   capability diagram. No prose proposal doc/deck.

## Decision table

| # | Decision | Choice |
|---|----------|--------|
| 1 | Deliverables | Thin marketplace + message-intelligence engine (both code) |
| 1b | Platform proposal | Architecture diagram + capability diagram only |
| 2 | Stack | Python **FastAPI** backend + **React** (Vite, TS) frontend |
| 3 | Data source | Scrape **only** TaskRabbit public category taxonomy (one-time, cached, with committed synthetic fallback); **all chat text generated synthetically** with hidden ground-truth labels |
| 3b | Input channel | **Customer chat conversations** (multi-turn threads), not isolated messages |
| 4 | Engine output | **Full chain**: per-message classify + extract entities + confidence + recommended action → write-back into marketplace; **plus** aggregate insights dashboard |
| 5 | AI mode | **Dual-mode**: Claude **Opus 4.8** (`claude-opus-4-8`) live path + seeded deterministic mock for offline / eval / CI |
| 6 | Corpus | ~120 seeded multi-turn conversations (4–12 turns), fully labeled; **~25 hand-verified golden set**; eval scores accuracy/F1 per field |
| 7 | UI | **Insights/Triage console** (centerpiece) + **conversation drill-down** (chat ⟷ extracted insights); marketplace kept thin (request→match→booking) |
| 8 | Definition of done | Golden-set thresholds met, both modes pass, tests green, lint/type clean, e2e demo, diagrams match build |

## Definition of done (success bar)

- **Eval (golden set ~25 convos):**
  - category F1 ≥ 0.85
  - route / escalation F1 ≥ 0.90  *(the actionable decision)*
  - entity extraction ≥ 0.80
  - sentiment ≥ 0.80
- Both **mock** and **live (Opus)** modes pass.
- `pytest` + `vitest` green; `ruff` + `mypy` clean.
- End-to-end demo path works: load corpus → dashboard populates → drill into a
  complaint conversation → engine flags escalate / human-review → marketplace
  shows job created / routed.
- Architecture + capability diagrams are consistent with the built system.

## Flags / caveats (surfaced, not blocking)

- **Opus-live vs "plenty of messages":** Opus is a cost/latency mismatch at real
  volume but fine for a ~120-convo demo; mock mode carries CI/bulk. If real
  volume is ever processed, drop the live path to Sonnet.
- **TaskRabbit ToS:** taxonomy fetch is one-time, cached, public-category-list
  only, with a committed synthetic fallback so the build is reproducible offline
  and never depends on a live scrape.

## Build order (eval-first)

1. Scaffold repo (backend / frontend / diagrams).
2. Synthetic corpus generator + taxonomy (cached/fallback) — **first**, because
   nothing can be measured without it.
3. Golden set (~25 hand-verified) + eval harness with thresholds.
4. Message-intelligence engine (classify/extract/route, dual-mode).
5. Thin marketplace (request → match → booking) + write-backs.
6. React UI (Insights console + drill-down + thin marketplace).
7. Architecture + capability diagrams.
8. Verify against the full bar.
