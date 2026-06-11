// Node-side inference: load the exported model.json from disk (once), then
// delegate to the runtime-agnostic predictWithModel. The pure prediction logic
// lives in predict_core.js so the browser UI runs the identical code path.

import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

import { featureOrder } from './features.js';
import { predictWithModel } from './predict_core.js';

let cachedModel = null;

function defaultModelPath() {
  return process.env.PRICING_MODEL_PATH || fileURLToPath(new URL('../model.json', import.meta.url));
}

export function loadModel() {
  if (cachedModel) return cachedModel;
  const model = JSON.parse(readFileSync(defaultModelPath(), 'utf8'));
  if (JSON.stringify(featureOrder(model.spec)) !== JSON.stringify(model.feature_order)) {
    throw new Error('feature order in model.json does not match the JS feature builder');
  }
  cachedModel = model;
  return cachedModel;
}

// Tests load different fixtures; let them reset the module cache.
export function resetModelCache() {
  cachedModel = null;
}

export function predict(record) {
  return predictWithModel(record, loadModel());
}
