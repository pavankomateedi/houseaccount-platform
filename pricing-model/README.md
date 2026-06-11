# HouseAccount AI Pricing Model

A booking-time price estimator for home-service jobs. Given a booking payload it
returns a price range (`estimate_lo`/`estimate_hi`), a point `estimate_midpoint`,
and a calibrated `confidence` that drops below 0.5 for out-of-distribution jobs —
matching the Appendix A API contract and beating the baseline MAPE.

The model is trained in Python and exported to a small `model.json`, then served
by a **pure Node Netlify function** (no Python at request time, inference is a
dot product, well under the 2s budget).

## Quick start (under 15 minutes)

```bash
cd pricing-model

# 1. Python env + deps
python -m venv .venv && . .venv/Scripts/activate    # macOS/Linux: source .venv/bin/activate
pip install -r requirements-dev.txt   # dev/training only; NOT needed to deploy

# 2. Node deps (for the endpoint + its tests)
npm install

# 3. Get data. The real dataset is provided (see "Data" below). For local dev
#    without it, generate synthetic data (clearly flagged, never scored as real):
python data/make_synthetic.py

# 4. Train + evaluate. Writes functions/model.json on a passing run.
python eval/run_eval.py --data data/pricing_synthetic.csv --allow-synthetic

# 5. Run the tests
pytest                 # Python: domain, data, features, model, calibration
npm test               # Node: contract, calibration, feature-parity, edge, clarify

# 6. Build + open the validation UI
python eval/export_ui.py --data data/pricing_synthetic.csv --allow-synthetic
cd public && python -m http.server 8787      # open http://127.0.0.1:8787
```

With the **real** dataset, drop it at `data/pricing_real.csv` and run the same
commands **without** `--allow-synthetic` (and `--data data/pricing_real.csv`).

## How pricing works

1. **Features** ([pricing/features.py](pricing/features.py)) — category and deadline one-hots,
   booking month, and scope signals pulled from `job_description` with simple
   regexes (word count, largest quantity, materials-supplied flag). The feature
   layout is described by a `FeatureSpec` baked into `model.json` so the JS side
   builds identical vectors.
2. **Model** ([pricing/model.py](pricing/model.py)) — three quantile linear regressors (10/50/90)
   predict the **log-ratio of the final price to the baseline estimate**, not the
   price from scratch. The model anchors at a strong baseline and only moves where
   scope features justify it; `price = baseline * exp(ratio)`.
3. **Calibration** ([pricing/calibration.py](pricing/calibration.py)) — confidence is graded by
   interval width and forced below 0.5 for any OOD condition: midpoint > $5,000,
   interval > 3x the median, or a non-production category.

The trained model serializes to coefficients in `functions/model.json`; the
endpoint evaluates them in JS ([functions/_lib/predict_core.js](functions/_lib/predict_core.js)).

See [MODELING_APPROACH.md](MODELING_APPROACH.md) for the full rationale.

## Data

The dataset is a **provided project input** (the HouseAccount Google Sheet,
1,432 rows, 411 priced). It is the basis for evaluation, so **we never fabricate
training/eval data** — that would fail HouseAccount's held-out scoring.

For local development without the sheet, [data/make_synthetic.py](data/make_synthetic.py) generates
a realistic stand-in. It stays detectably synthetic (job_ids are not SHA-256),
and the harness **refuses to run on it unless you pass `--allow-synthetic`**,
which stamps every output and the served `model_version` as `-synthetic`. This
guard is what stops fabricated numbers from ever being mistaken for real ones.

## Evaluation

[eval/run_eval.py](eval/run_eval.py) is the gate. It reports baseline vs model on three views and
exits non-zero unless the model beats baseline where it must:

- **blended** (full priced set) — must beat the published 11.6% baseline
- **held-out** (unseen test split) — must beat baseline on the same rows
- **held-out real-like** (high-baseline-error tail) — informational

Current numbers are **SYNTHETIC** (placeholder until the real CSV lands):

```text
blended    baseline 15.74%  model 8.51%   beats
held-out   baseline 17.01%  model 9.94%   beats
real-tail  baseline 38.30%  model 12.54%  beats
```

[eval/diagnose.py](eval/diagnose.py) prints distributions (run it first on real data).

## API contract (Appendix A)

`POST /.netlify/functions/pricing-estimate`, `Authorization: Bearer <secret>`.

```bash
curl -X POST http://localhost:8888/.netlify/functions/pricing-estimate \
  -H "Authorization: Bearer $GAUNTLET_PRICING_SECRET" \
  -H "Content-Type: application/json" \
  -d '{"job_id":"abc123","service_category":"Plumbing","zip_code":"78704",
       "job_description":"Replace 3 plumbing fixtures","original_estimate":360}'
# -> { "ok": true, "job_id": "abc123", "estimate_lo": ..., "estimate_hi": ...,
#      "estimate_midpoint": ..., "confidence": ..., "model_version": "..." }
```

Request/response are validated by [schema/request.schema.json](schema/request.schema.json) and
[schema/response.schema.json](schema/response.schema.json); errors (400/401/405) follow the contract.

## Web app (static, multi-page)

`public/` is a no-build static site with two linked areas, cross-linked in the header:

- **`index.html` — the storefront** (home): a services catalog (companies + individual
  pros, provider profiles, Shopify-style service detail pages, cart) in the
  HouseAccount.AI brand. It's the design-handoff prototype, run as self-contained
  React-in-Babel (no build step). Seed data: [public/houseaccount/data.js](public/houseaccount/data.js).
- **`pricing.html` — the Instant Estimate flow**: a market/ZIP → AI estimate →
  provider pricing options → checkout/enquiry → persisted bookings tool. It runs
  the **same tested inference modules** in the browser (`predict_core.js`,
  `calibration.js`, `features.js`, `clarify.js`) and also shows the eval
  scoreboard and dataset behind "Behind the model". Re-skinned to match the
  storefront design.

Build the pricing data + assets with `npm run build:ui` (or
`python eval/export_ui.py ...`), then `npm run serve` and open
<http://127.0.0.1:8787> (storefront) / `/pricing.html` (estimator).

## Project layout

```text
pricing-model/
  pricing/        domain + app: metrics, data, calibration, features, model, evaluation, markets
  functions/      Netlify endpoint (pricing-estimate.js) + _lib/ pure JS (mirrors pricing/)
  eval/           diagnose.py, run_eval.py (gate), export_ui.py, e2e_smoke.py, goldenset/
  schema/         request/response + markets/providers JSON Schema
  public/         static site: index.html (storefront) + houseaccount/ assets;
                  pricing.html + the pure JS modules + generated *.json
  data/           make_synthetic.py; pricing_synthetic.csv (dev); pricing_real.csv (you provide)
  tests/          pytest suite mirroring pricing/
  .githooks/      opt-in pre-commit (runs the unit suites)
```

## Environment

- `GAUNTLET_PRICING_SECRET` — bearer secret; the function throws on cold start if unset.
- `PRICING_MODEL_PATH` — optional override of the `model.json` path (used in tests).

## More docs

- [MODELING_APPROACH.md](MODELING_APPROACH.md) — model, features, calibration, assumptions, limits
- [DEPLOY.md](DEPLOY.md) — local run + Netlify deploy + staging
- [AI_USAGE.md](AI_USAGE.md) — how AI tools were used to build this
- [AGENTIC_AI_CHECKLIST.md](AGENTIC_AI_CHECKLIST.md) — compliance pass
