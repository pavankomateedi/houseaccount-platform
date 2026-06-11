// Confidence calibration and OOD rules — JS mirror of pricing/calibration.py.
// Both implementations are driven by the same golden cases
// (eval/goldenset/calibration_cases.json) so they cannot drift.
//
// Contract (Appendix A): any single OOD condition forces confidence < 0.5.
// Invariant 0.9 * 0.5 = 0.45 < 0.5 guarantees it.

export const OOD_MIDPOINT_USD = 5000;
export const OOD_INTERVAL_MULTIPLE = 3;

const MAX_BASE_CONFIDENCE = 0.9;
const MIN_BASE_CONFIDENCE = 0.5;
const OOD_PENALTY = 0.5;

// The 8 dataset categories mapped from the 10 production verticals. Mirrors
// PRODUCTION_CATEGORIES in pricing/calibration.py.
export const PRODUCTION_CATEGORIES = new Set([
  'Electrical',
  'Cleaning',
  'Handyman',
  'HVAC',
  'Landscaping',
  'Pest Control',
  'Plumbing',
  'Exterior',
]);

export function oodFlags(midpoint, lo, hi, category, medianInterval) {
  const price = midpoint > OOD_MIDPOINT_USD;
  const interval = hi - lo > OOD_INTERVAL_MULTIPLE * medianInterval;
  const categoryOod = !PRODUCTION_CATEGORIES.has(category);
  return { price, interval, category: categoryOod, any: price || interval || categoryOod };
}

function baseConfidence(midpoint, lo, hi) {
  if (midpoint <= 0) return MIN_BASE_CONFIDENCE;
  const relativeWidth = (hi - lo) / midpoint;
  const graded = 0.95 - 0.45 * relativeWidth;
  return Math.max(MIN_BASE_CONFIDENCE, Math.min(MAX_BASE_CONFIDENCE, graded));
}

export function calibrateConfidence(midpoint, lo, hi, category, medianInterval) {
  let confidence = baseConfidence(midpoint, lo, hi);
  const flags = oodFlags(midpoint, lo, hi, category, medianInterval);
  if (flags.price) confidence *= OOD_PENALTY;
  if (flags.interval) confidence *= OOD_PENALTY;
  if (flags.category) confidence *= OOD_PENALTY;
  return Math.max(0, Math.min(1, confidence));
}
