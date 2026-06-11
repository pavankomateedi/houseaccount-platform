// Pure, runtime-agnostic inference: given a record and a parsed model, produce
// the estimate. No Node/browser APIs here, so this exact code runs in both the
// Netlify function (via infer.js) and the validation UI (in the browser).
//
// Mirrors pricing.model.PricingModel.predict_frame: standardize features, each
// quantile predicts a log-ratio to the baseline, price = baseline * exp(ratio),
// order the bounds, then calibrate confidence.

import { calibrateConfidence } from './calibration.js';
import { baselineMidpoint, buildVector, normalizeCategory } from './features.js';

function dot(a, b) {
  let sum = 0;
  for (let i = 0; i < a.length; i += 1) sum += a[i] * b[i];
  return sum;
}

const round2 = (value) => Math.round(value * 100) / 100;

export function predictWithModel(record, model) {
  const category = normalizeCategory(record.service_category);
  const normalized = { ...record, service_category: category };

  const vector = buildVector(normalized, model.spec);
  const { mean, scale } = model.standardizer;
  const standardized = vector.map((value, i) => (value - mean[i]) / scale[i]);
  const baseline = baselineMidpoint(normalized, model.spec);

  const bounds = ['lo', 'mid', 'hi']
    .map((name) => {
      const quantile = model.quantiles[name];
      return baseline * Math.exp(dot(standardized, quantile.coef) + quantile.intercept);
    })
    .sort((a, b) => a - b);
  const [lo, mid, hi] = bounds;

  const confidence = calibrateConfidence(mid, lo, hi, category, model.median_predicted_interval);
  return {
    estimate_lo: round2(lo),
    estimate_hi: round2(hi),
    estimate_midpoint: round2(mid),
    confidence: round2(confidence),
    model_version: model.model_version,
  };
}
