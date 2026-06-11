# Deployment Guide

## Prerequisites

- Python 3.11+
- Node.js 18+ (developed on 24)
- Netlify CLI (optional, for local serving / deploy)

## Local setup

```bash
cd pricing-model
python -m venv .venv && . .venv/Scripts/activate    # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
npm install
```

## Build the model artifact

The endpoint serves predictions from `functions/model.json`. Produce it with the
eval gate (it writes the artifact only on a passing run).

```bash
# Development (synthetic data — output is stamped -synthetic):
python data/make_synthetic.py
python eval/run_eval.py --data data/pricing_synthetic.csv --allow-synthetic

# Real data (drop the provided CSV first), no flag:
python eval/run_eval.py --data data/pricing_real.csv
```

Commit `functions/model.json` so it deploys with the function.

## Run the tests

```bash
pytest          # Python suite (domain, data, features, model, calibration, metrics)
npm test        # Node suite (contract, calibration, feature parity, edge/OOD, clarify)
```

## Run the endpoint locally

```bash
export GAUNTLET_PRICING_SECRET="local-dev-secret"     # Windows: set GAUNTLET_PRICING_SECRET=...
netlify dev                                            # serves functions on http://localhost:8888

curl -X POST http://localhost:8888/.netlify/functions/pricing-estimate \
  -H "Authorization: Bearer local-dev-secret" \
  -H "Content-Type: application/json" \
  -d '{"job_id":"abc123","service_category":"Plumbing","zip_code":"78704",
       "job_description":"Replace 3 plumbing fixtures","original_estimate":360}'
```

The function throws on cold start if `GAUNTLET_PRICING_SECRET` is unset, and
returns `500 {"error":"Estimate failed"}` if `model.json` is missing.

## Run the web app locally

```bash
npm run build:ui      # = python eval/export_ui.py --data data/pricing_synthetic.csv --allow-synthetic
npm run serve         # = python -m http.server 8787 --directory public
# open http://127.0.0.1:8787          -> storefront (index.html)
# open http://127.0.0.1:8787/pricing.html  -> Instant Estimate flow
```

Both pages are static and run in the browser. The pricing page runs inference
from `public/model.json` (no function needed); the storefront compiles its JSX
via Babel from a CDN (needs internet on first load).

## End-to-end UI smoke test

```bash
pip install playwright && python -m playwright install chromium   # one-time
python eval/e2e_smoke.py        # starts a server, drives storefront + pricing flow, exits non-zero on failure
```

## Deploy to Netlify

Config lives in [netlify.toml](netlify.toml) (functions dir `functions`, publish dir `public`).

1. Connect the GitHub repo at [app.netlify.com](https://app.netlify.com) (Add new site -> Import).
2. Build settings: build command `npm install`, functions directory `functions`,
   publish directory `public`.
3. Set environment variable `GAUNTLET_PRICING_SECRET` (Site settings -> Environment).
4. Ensure `functions/model.json` is committed. Deploy on push, or `netlify deploy --prod`.

Endpoint URL: `https://<site>.netlify.app/.netlify/functions/pricing-estimate`.

## Environment variables

- `GAUNTLET_PRICING_SECRET` — bearer secret (required).
- `PRICING_MODEL_PATH` — optional override of the model.json path (tests use this).

## Rollback

```bash
git revert <commit>     # revert code/model change, redeploy
```

Or roll back to a previous deploy in the Netlify dashboard (Deploys -> a prior
deploy -> Publish).

## Troubleshooting

- `GAUNTLET_PRICING_SECRET env var is required` — set the env var before serving.
- `500 {"error":"Estimate failed"}` — usually `functions/model.json` is missing;
  run the eval gate to produce it.
- `Refusing to proceed: dataset looks synthetic` — you ran the harness on
  synthetic data without `--allow-synthetic`. Add the flag for dev, or drop the
  real CSV at `data/pricing_real.csv`.

## Out of scope (current)

- **Posting to the HouseAccount staging `bookings-create` endpoint** is deferred.
  This service is the receiving side of the contract; the outbound demo client is
  a tracked follow-up.
- Load testing, caching headers, and async webhooks are out of scope per the brief.
