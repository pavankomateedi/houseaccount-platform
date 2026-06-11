# AI Usage

How AI tooling was used to build this project, per the brief's template.

## Tools used

- **Claude Code (Claude Opus 4.8)** — the primary coding agent for the entire
  build: planning, code generation, refactoring, test authoring, debugging, and
  building the validation UI. Operated against a set of repo coding rules
  (clean-architecture / clean-code / simplicity-first / testing-python) loaded at
  session start.
- **Playwright (driven by the agent)** — headless browser verification of the
  validation UI (rendering, in-browser inference, OOD flags, clarifying questions).
- **scikit-learn / pandas / numpy** — the modeling stack (not AI, but the agent
  chose and wired them). `QuantileRegressor` for the quantile-linear model.

Notably, **no LLM is used at request time** — scope extraction is deterministic
regex, so inference is free, fast, and reproducible. AI was a build-time tool,
not a runtime dependency.

## Significant prompts (the ones that shaped the architecture)

1. **"Build to the requirements; start with goldenset, evals, harness, JSON, and
   tools, then code."** Set the order: build the verification harness and contract
   first, then iterate the model against measured results.
2. **"Did the requirement say they will provide the data?"** Forced an honest read
   of the brief — the dataset is a provided input and the eval basis — which led
   to the rule *never fabricate training/eval data* and the synthetic-data guard.
3. **Architecture decision prompt (agent-posed, user-chosen):** Node-only Netlify
   function (train in Python, export to JSON, infer in JS) + tabular ML with
   text features. This drove the linear (JSON-portable) model and the
   Python<->JS parity design.
4. **"Make up synthetic data ... and ignore the API integration for now."** Led to
   a realistic generator that reproduces the brief's baseline structure, plus the
   `--allow-synthetic` guard so fake numbers can never pose as real.
5. **"I'd like a UI to validate/see the data."** Produced the browser console that
   reuses the exact tested inference modules (no reimplementation).
6. **"More data for quick chores vs major appliances, and ask clarifying questions
   with each estimate."** Reweighted the generator toward quick chores and added
   the tested `clarify.js` question engine (kept in the UI, not the locked API
   response).

The single most important *technical* pivot the agent made: switching the model
target to the **log-ratio of price to the baseline estimate** after the harness
showed a from-scratch model couldn't beat a strong baseline.

## Validation steps for AI-generated code

- **Automated tests** — 52 pytest (metrics, data + synthetic guard, features,
  model pipeline, calibration invariants) and 35 Node tests (HTTP contract,
  calibration golden parity, Python<->JS feature parity, edge/OOD, clarify). Run
  via `pytest` and `npm test`.
- **Cross-runtime parity** — shared golden cases and a feature-parity fixture
  assert the JS endpoint and Python model compute identically.
- **Eval gate** — `eval/run_eval.py` exits non-zero unless the model beats
  baseline; it refuses synthetic data unless explicitly allowed.
- **UI verification** — Playwright confirmed the page renders with no JS errors
  and that OOD inputs produce low confidence + the expected flags.

### Hallucinations / bad output caught and fixed

1. **Prior build was trained on synthetic data and the endpoint returned
   `Math.random()`.** Caught on first read; the whole thing was rebuilt and a
   synthetic-data guard added so it can't recur silently.
2. **`mape` used `if not predicted:`** — ambiguous on numpy arrays; the harness
   crashed. Fixed to a length check and added an array regression test.
3. **`is_synthetic` returned `numpy.bool_`** instead of Python `bool`; caught by a
   strict `is True` test.
4. **First synthetic generator encoded the price signal as a per-template
   *normalized* value the model couldn't recover from raw features** — the task
   was unlearnable, so the model couldn't beat baseline. Rewritten so the signal
   is a clean function of the actual extracted features.
5. **Request payloads use `original_estimate_lo/hi`, not `estimate_lo/hi`** — the
   feature resolver was dropping request bounds; fixed in both languages with tests.
6. **The UI's prefilled example was out-of-distribution for the synthetic model**
   (a realistic $1,850 water heater vs synthetic Plumbing ~$350), producing a weird
   low-confidence result; aligned the demo input to the data.

## Reflection

**Where AI helped most.** Standing up the full layered architecture, the
verification harness, and the Python<->JS parity machinery quickly; and relentless
test-writing that caught real bugs (numpy truthiness, bool typing, the request
field mismatch). The agent was also good at *refusing to proceed dishonestly* —
flagging the synthetic-data trap and building guards instead of papering over it.

**Where AI produced bad output.** It needed several iterations to design synthetic
data that was both realistic *and* learnable (first version unlearnable, second
made the baseline implausibly bad). Left unchecked, an agent will happily generate
plausible-but-meaningless numbers — exactly what the previous build shipped.

**What I'd do differently.** Establish the "real data only for eval, synthetic is
dev-only and must be labeled" rule on day one. Define the verification harness and
the metric before writing any model code (the brief's own instinct, and it paid
off). And treat any "we beat the baseline" claim as false until a held-out gate
says so on real data.
