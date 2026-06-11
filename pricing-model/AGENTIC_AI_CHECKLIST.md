<!--
  AGENTIC AI DEVELOPMENT CHECKLIST — filled for the HouseAccount AI Pricing Model.
  Legend: [x] done & verified · [ ] not done (GAP noted) · [~] partial · [N/A] not applicable (reason given).
  This is an ML request/response pricing SERVICE, not an autonomous tool-using agent —
  so agent-loop / prompt / multi-agent items are marked N/A with rationale rather than skipped silently.
-->

# 🤖 Agentic AI Development Checklist

## Project Info

| Field | Value |
|---|---|
| **Project name** | HouseAccount AI Pricing Model |
| **Owner** | Pavan Komateedi (pavan.kom@gmail.com) |
| **Team / stakeholders** | HouseAccount (Claudio — technical contact); Gauntlet capstone evaluators |
| **Start date** | 2026-06 |
| **Target ship date** | TBD (blocked on real-data eval) |
| **Status** | ☑ Building · ☐ Eval (harness ready; numbers pending real CSV) |
| **Autonomy level** | ☑ Suggest only (returns estimate + confidence for downstream routing; takes no action) |
| **Last reviewed** | 2026-06-09 |

**One-line goal:**
> Given a HouseAccount booking payload, return a price estimate (lo/hi/midpoint) plus a calibrated confidence that drops below 0.5 for out-of-distribution jobs — beating the baseline MAPE (11.6% blended, ~40% real-only) in under 2 seconds.

---

## 1. Scope & Requirements

- [x] Defined the single job the agent must do (one-liner above)
- [x] Listed concrete tasks: accept Appendix-A payload → estimate + confidence; calibrate OOD; beat baseline MAPE; post to staging endpoint
- [x] Listed out-of-scope tasks: load testing, caching layer, webhooks, multi-tenant isolation (per brief "Out of scope"); **do not synthesize training/eval data**; do not hardcode pricing tables
- [x] Identified the user: HouseAccount marketplace booking flow (machine consumer) + engineers integrating the endpoint
- [x] Decided autonomy level: Suggest only (recorded above)
- [x] Defined measurable success: blended MAPE < 11.6%, real-only held-out MAPE < baseline, confidence < 0.5 on all 3 OOD conditions, response < 2s
- [x] Defined acceptable failure modes: low-confidence (<0.5) estimate routes the job to human/escalation downstream — this is the *designed* safe failure, not a crash
- [x] Identified hard constraints: < 2s/request, secrets via env only, no hardcoded lookup tables, accept-don't-reject OOD inputs
- [x] Confirmed an agent is the right tool: **it isn't an agent** — a deterministic ML model behind a thin API is the correct, lower-risk choice (recorded as a deliberate decision)

> Notes: "Agentic" framing is intentionally rejected here; the brief wants a reproducible, <2s, model-backed endpoint, not an autonomous loop.

## 2. Architecture & Design

- [x] Chose the pattern: single stateless request/response model service (data → features → quantile-linear model → calibration → JSON)
- [N/A] Control loop (plan→act→observe→reflect): no agentic loop; one synchronous inference per request
- [x] Decided where state lives: stateless function + a serialized `model.json` artifact (no per-request state)
- [x] Memory strategy: none — discard after response (no session memory by design)
- [N/A] Context budget / compaction: no LLM context at runtime
- [x] Chose model per task: quantile **linear** regression on log-price (deterministic, JSON-portable to JS, <10ms) — chosen over LLM/trees for latency + Node-only inference; tree-export documented as escalation
- [x] Human-in-the-loop checkpoint: confidence < 0.5 surfaces OOD jobs for downstream human routing (we report confidence, never auto-act)
- [x] Stopping condition: single response; 500 `Estimate failed` if inference errors
- [x] Graceful degradation: missing optional fields fall back to spec defaults; missing/old `model.json` → 500 (not a crash); category normalization tolerates unknown inputs

## 3. Tools & Integrations

- [x] Listed every module/"tool": [data.py](pricing/data.py), [features.py](pricing/features.py), [model.py](pricing/model.py), [calibration.py](pricing/calibration.py), [_lib/infer.js](functions/_lib/infer.js), [_lib/contract.js](functions/_lib/contract.js); eval harness
- [x] Tool descriptions & schemas: JSON Schemas ([request](schema/request.schema.json), [response](schema/response.schema.json)) + module docstrings
- [x] Validated/sanitized inputs: required-field check, numeric coercion, ZIP pattern, JSON-parse guard
- [x] Outputs concise & machine-readable: fixed JSON response (Appendix A wrapper)
- [x] Tool errors recoverable/informative: error bodies match Appendix A (`{ "error": "..." }`)
- [~] Timeouts/retry for external calls: N/A at request time (pure local inference, no network/DB); the *integration* POST to the staging endpoint will need timeout/retry — **GAP until that wiring is added**
- [x] Least-privilege: single shared bearer secret; endpoint does no DB/network/filesystem writes
- [N/A] Destructive/irreversible tools: none — estimate is read-only
- [x] Tested each in isolation: 51 Python + 28 JS unit/contract tests
- [x] Removed overlapping/ambiguous tools: deleted the old synthetic pipeline and the `Math.random` mock

## 4. Prompting & Instructions

- [N/A] **Entire section N/A at runtime** — there is no LLM or prompt in the request path; pricing is a deterministic ML computation.
- [x] Build-time AI usage (coding agents, prompts that shaped architecture) is documented separately in [AI_USAGE.md](AI_USAGE.md) per the brief's requirement.

## 5. Safety, Security & Guardrails

- [N/A] Prompt-injection threat model: no LLM consumes content at runtime
- [x] Treated external/retrieved content as untrusted: `job_description` is free text but only **regex feature-extracted** — never executed, never `eval`'d, never sent to an LLM
- [~] Input guardrails: schema validation present; we **intentionally do not reject** OOD inputs (brief mandates pass-through with low confidence)
- [x] Output guardrails: fixed response schema (`additionalProperties:false` enforced in tests), confidence clamped to [0,1], no PII / no echo of description, short error messages
- [x] Authz/authn on every call: constant-time bearer (`timingSafeEqual`), boot-time secret enforcement
- [x] Isolated execution: stateless function, no code execution, no shell
- [x] Secrets out of prompts/logs: `GAUNTLET_PRICING_SECRET` via env; handler logs nothing sensitive
- [~] Spend/rate limits: rate limiting is **optional** per brief and **not implemented** — 429 shape is documented for future add (GAP if abuse protection is required)
- [N/A] Human approval for irreversible/financial actions: none exist
- [~] Kill switch / circuit breaker: disable via Netlify (deploy-level); no in-app breaker (acceptable for stateless read-only)
- [x] Data privacy/compliance: dataset is pre-sanitized (PII stripped, hashed IDs); we introduce no new PII

## 6. Evaluation & Testing  ← core; partially blocked on real data

- [x] Golden dataset with expected outcomes: [calibration](eval/goldenset/calibration_cases.json), [contract](eval/goldenset/contract_cases.json), [edge/OOD](eval/goldenset/edge_request_cases.json). **Accuracy golden = the real 411 priced rows (pending CSV).**
- [x] Metrics defined: blended & real-only MAPE, median APE, confidence thresholds, interval ordering
- [x] Automated eval harness: [run_eval.py](eval/run_eval.py) (gate + exit code) and [diagnose.py](eval/diagnose.py)
- [x] Edge / adversarial / ambiguous inputs tested: OOD categories, >$5k, wide intervals, missing optionals, kebab-case, malformed JSON, blank fields
- [~] End-to-end trajectories: endpoint contract tested end-to-end; full model accuracy eval is end-to-end but **awaits real data**
- [x] Regression tests: 79 total (pytest 51 + node 28)
- [~] Red-team / jailbreak: auth/validation/method negative tests done; no LLM jailbreak surface — limited applicability
- [ ] **Baseline score established before optimizing: NOT YET — blocked on `data/pricing_real.csv`** (GAP — the one substantive blocker)
- [x] Quality bar defined: beat 11.6% blended AND baseline real-only (defined; not yet met)
- [~] Feed failures back into dataset: harness supports it; not yet exercised on real data

> **Quality bar:** `run_eval` must report blended MAPE < 11.6% AND held-out model MAPE < held-out baseline, with exit code 0.

## 7. Observability & Cost

- [~] Logged traces: minimal by design (no request-body logging for privacy); **GAP — add structured, PII-safe request/version logging for production**
- [ ] Inspectable per-session traces: not built (GAP / out of capstone scope)
- [N/A] Token usage/cost: no LLM — runtime inference is free local compute
- [~] Latency tracking: not instrumented; <2s guaranteed by design (linear inference <10ms, no network)
- [ ] Alerting (errors/cost/loops): not built (GAP / out of capstone scope)
- [~] Runs tagged by version: `model_version` echoed in every response (partial — no aggregation)
- [ ] Metrics dashboard: not built (out of capstone scope)

## 8. Deployment

- [x] Pinned model versions & deps: [requirements-dev.txt](requirements-dev.txt) pinned (dev/training only); [package.json](package.json)
- [x] Externalized config: secret + `PRICING_MODEL_PATH` via env
- [x] Secrets in a manager: Netlify environment variables (not a dedicated vault — adequate for single shared secret)
- [~] Staging environment: HouseAccount provides the staging booking endpoint; integration POST not yet wired (GAP)
- [N/A] Gradual/canary rollout: out of capstone scope
- [~] Rollback: git revert + redeploy; `model.json` is versioned — no automated rollback
- [~] Runbooks: [DEPLOY.md](DEPLOY.md) exists (pending rewrite to match new architecture)
- [N/A] Load-tested for concurrency: explicitly out of scope per brief

## 9. Monitoring & Maintenance

- [N/A] Live monitoring / real-transcript review / production-failure feedback / cost passes: not yet deployed — these are **post-ship** activities. Recorded as the maintenance plan, not yet active.
- [x] Watching for model deprecations / re-running evals after changes: `run_eval` + `pytest` + `npm test` are the regression gate to re-run on any change.

## 10. Documentation & Ownership

- [~] Architecture/tools/data-flow documented: [MODELING_APPROACH.md](MODELING_APPROACH.md) (pending rewrite to match the rebuilt architecture)
- [~] Known limitations & failure modes: documented; refresh with real-data limitations after eval
- [x] Owner assigned: Pavan (above)
- [~] Eval suite documented: commands exist; README how-to-run pending rewrite
- [x] Key design decisions recorded: this build log + repo `DECISIONS.md`; Node-only/linear/parity choices captured
- [~] User-facing guidance: README + Appendix-A contract (README pending rewrite)

---

## ✅ Pre-Ship Gate — NOT YET PASSED

- [ ] **Eval score meets the quality bar — NO (blocked on real `data/pricing_real.csv`)**
- [~] Guardrails tested against red-team attempts — partial (no LLM surface; auth/validation covered)
- [~] Cost and latency within budget — latency yes by design; not formally measured
- [N/A] Human approval on irreversible actions — no irreversible actions exist
- [~] Rollback tested and runbooks written — git-based; DEPLOY.md pending rewrite
- [x] Owner assigned — yes · [ ] Monitoring live — NO (not deployed)

**Verdict:** Engineering foundation, contract conformance, calibration, and edge-case robustness are **done and test-green**. The project is **not shippable yet** for two reasons: (1) no baseline-beating MAPE on the real dataset (blocked on the provided CSV), and (2) observability/monitoring/staging-integration are not built (largely out of capstone scope, flagged as GAPs). Once the real CSV lands and `run_eval` exits 0, the only remaining ship items are the integration POST to staging and basic production logging.

**Sign-off:** _______________  **Date:** ___________
