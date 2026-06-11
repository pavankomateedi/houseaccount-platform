# Modeling Approach

## Problem

Predict a booking-time price (range + midpoint) and a calibrated confidence from
a free-text booking payload, beating the previous-model baseline on MAPE while
keeping the endpoint under 2 seconds. Scope is not given as structured fields —
it has to be extracted from `job_description`.

## Data

- Provided dataset: 1,432 jobs across 18 categories; 411 have a `final_price`
  (the supervised signal and eval basis). ~1,033 real ZIPs.
- Categories are title-case in the dataset, kebab-case in production seeds; we
  normalize on read ([pricing/data.py](pricing/data.py)).
- **We do not synthesize training/eval data.** A development-only synthetic
  generator exists ([data/make_synthetic.py](data/make_synthetic.py)) but is guarded: the harness refuses
  to treat it as real unless `--allow-synthetic` is passed, and it stamps all
  output `-synthetic`. See README "Data".

## Why this model

The baseline (`original_estimate`) is already decent on typical jobs, so a
from-scratch regressor tends to *lose* to it on the easy majority while only
occasionally winning. The fix — which is also what the brief hints at with
"blend against the baseline" — is to **predict a correction to the baseline**:

```text
target  = log(final_price) - log(baseline_midpoint)        # a log-ratio
predict = baseline_midpoint * exp(model_output)
```

The model anchors at the baseline (outputs ~0 where the estimate is already
right) and moves only where features justify it. This is robust: it rarely does
worse than baseline, and it gains exactly on the rows where scope signals predict
the deviation (the high-error "real" tail).

### Architecture

- **Quantile linear regression** (scikit-learn `QuantileRegressor`) at the 10th,
  50th, and 90th percentiles over standardized features. The median gives the
  midpoint; the 10/90 pair gives an asymmetric interval. Bounds are sorted to
  guarantee `lo <= mid <= hi`.
- **Linear by design**: coefficients export to a small `model.json`, so inference
  is a dot product the Netlify function runs in pure JS — no Python, no model
  server, trivially within the 2s budget. (If a linear model could not beat
  baseline on real data, the documented escalation is exporting a small tree
  ensemble to JSON with a JS tree-walker.)

### Features ([pricing/features.py](pricing/features.py))

A `FeatureSpec` (category vocab, deadline vocab, fallback medians) fully
describes the vector and is serialized into `model.json`, so the JS feature
builder ([functions/_lib/features.js](functions/_lib/features.js)) reproduces it exactly (enforced by a
parity test). Features:

- numeric: `log_original_estimate`, `log_estimate_interval`, `booking_month_num`,
  and scope from `job_description` — `log_desc_word_count`, `log_max_number`
  (largest quantity mentioned), `materials_supplied` (regex flag);
- one-hots: `service_category`, `deadline`.

Scope extraction is deliberately simple regex (not an LLM) so it is deterministic,
free per request, and trivially mirrored in JS. Requests carry
`original_estimate_lo/hi`; training rows carry `estimate_lo/hi`; the resolver
accepts either.

## Confidence calibration ([pricing/calibration.py](pricing/calibration.py))

Base confidence is graded by relative interval width (tight interval -> high
confidence), then multiplied by 0.5 for each out-of-distribution condition:

- `estimate_midpoint > $5,000`
- prediction interval `> 3x` the median predicted interval (baked into `model.json`)
- `service_category` outside the 10 production verticals

The invariant `max_base (0.9) * 0.5 = 0.45 < 0.5` guarantees that **any single
OOD condition drops confidence below 0.5** — verified by a grid test and shared
golden cases that both Python and JS run. OOD inputs are passed through with low
confidence, never rejected or capped (per the contract).

Production-category mapping (10 kebab slugs -> 8 dataset categories) is a judgment
call documented in `calibration.py`; e.g. `indoor-cleaning`/`exterior-cleaning`
-> `Cleaning`.

## Evaluation ([pricing/evaluation.py](pricing/evaluation.py), [eval/run_eval.py](eval/run_eval.py))

Three views, baseline (`original_estimate`) vs model:

1. **blended** — full-fit, scored on all 411 priced rows (the submission view);
   gate: beat the published 11.6% baseline.
2. **held-out** — trained on a seeded train split, scored on the unseen test
   split (the honest generalization estimate); gate: beat baseline on those rows.
3. **held-out real-like** — test rows whose baseline APE is large (proxy for the
   genuinely-real ~40%-baseline rows); informational.

MAPE/median APE are pure functions in [pricing/metrics.py](pricing/metrics.py). The harness writes
`functions/model.json` only on a passing run.

### Current results (SYNTHETIC — placeholder until the real CSV)

```text
blended    baseline 15.74%  model 8.51%
held-out   baseline 17.01%  model 9.94%
real-tail  baseline 38.30%  model 12.54%
```

On synthetic data the model beats baseline partly **by construction** (the
generator's scope signal is recoverable from the model's features). This
validates the pipeline end to end; it is not a claim about real-world accuracy.

## Assumptions and limitations

- Scope lives in the description text; jobs with terse descriptions get wider
  intervals and lower confidence (and trigger clarifying questions in the UI).
- Linear log-ratio captures multiplicative scope effects well; strongly
  non-linear interactions would need the tree-export escalation.
- ZIP is currently only a passthrough field, not yet joined to census/income
  data — an obvious next lever for real-data accuracy.
- Confidence is a heuristic calibration, not a learned probability; it is tuned
  to satisfy the contract's OOD threshold, not to be a calibrated p-value.

## What changes with the real dataset

Drop `data/pricing_real.csv` and rerun `diagnose` -> `run_eval` -> `export_ui`
without `--allow-synthetic`. `diagnose` confirms the OOD thresholds against the
real distribution (e.g. that $5k is ~the 95th percentile); `run_eval` produces
the real MAPE numbers and the production `model.json`.
