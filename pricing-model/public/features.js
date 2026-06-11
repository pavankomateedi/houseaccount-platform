// Feature engineering — JS mirror of pricing/features.py.
// Vector layout and every extractor must match the Python side exactly, since
// the model coefficients in model.json were fit against Python's vectors. The
// feature parity test (functions/__tests__/features.test.mjs) enforces this.

// Canonical numeric features, in fixed order (matches NUMERIC_FEATURES in py).
export const NUMERIC_FEATURES = [
  'log_original_estimate',
  'log_estimate_interval',
  'booking_month_num',
  'log_desc_word_count',
  'log_max_number',
  'materials_supplied',
];

const MATERIALS_SUPPLIED =
  /\b(you supply|i supply|i'll supply|i provide|i'll provide|owner provides?|customer provides?|supply the|provided by (?:owner|customer|homeowner))\b/i;
const NUMBER = /\d+(?:\.\d+)?/g;

const CATEGORY_ALIASES = { hvac: 'HVAC' };

export function normalizeCategory(raw) {
  const collapsed = String(raw).trim().replace(/[-_]/g, ' ').replace(/\s+/g, ' ');
  const alias = CATEGORY_ALIASES[collapsed.toLowerCase()];
  if (alias) return alias;
  return collapsed
    .split(' ')
    .map((word) => (word ? word[0].toUpperCase() + word.slice(1).toLowerCase() : word))
    .join(' ');
}

export function extractScope(description) {
  const text = description === null || description === undefined ? '' : String(description);
  const words = text.split(/\s+/).filter((token) => token.length > 0);
  const numbers = (text.match(NUMBER) || []).map(Number);
  return {
    desc_word_count: words.length,
    max_number: numbers.length ? Math.max(...numbers) : 0,
    materials_supplied: MATERIALS_SUPPLIED.test(text) ? 1 : 0,
  };
}

export function featureOrder(spec) {
  return [
    ...NUMERIC_FEATURES,
    ...spec.category_vocab.map((category) => `cat::${category}`),
    ...spec.deadline_vocab.map((deadline) => `deadline::${deadline}`),
  ];
}

function toFloat(value) {
  if (value === null || value === undefined || value === '') return null;
  const parsed = Number(value);
  return Number.isNaN(parsed) ? null : parsed;
}

function resolveEstimate(record, spec) {
  // Training rows use estimate_lo/hi; API requests use original_estimate_lo/hi.
  const lo = toFloat(record.estimate_lo) ?? toFloat(record.original_estimate_lo);
  const hi = toFloat(record.estimate_hi) ?? toFloat(record.original_estimate_hi);
  let midpoint = toFloat(record.original_estimate);

  if (midpoint === null && lo !== null && hi !== null) midpoint = (lo + hi) / 2;
  if (midpoint === null) midpoint = spec.default_estimate;

  const interval = lo !== null && hi !== null ? Math.max(hi - lo, 0) : spec.default_interval;
  return { midpoint, interval };
}

// The baseline midpoint the model anchors its log-ratio correction to.
// Mirrors pricing.features.baseline_midpoint.
export function baselineMidpoint(record, spec) {
  return resolveEstimate(record, spec).midpoint;
}

function bookingMonthNumber(bookingMonth) {
  if (!bookingMonth) return 0;
  const match = /-(\d{2})$/.exec(String(bookingMonth));
  return match ? Number(match[1]) : 0;
}

export function buildFeatureRow(record, spec) {
  const { midpoint, interval } = resolveEstimate(record, spec);
  const scope = extractScope(record.job_description);

  const row = {
    log_original_estimate: Math.log1p(Math.max(midpoint, 0)),
    log_estimate_interval: Math.log1p(interval),
    booking_month_num: bookingMonthNumber(record.booking_month),
    log_desc_word_count: Math.log1p(scope.desc_word_count),
    log_max_number: Math.log1p(scope.max_number),
    materials_supplied: scope.materials_supplied,
  };

  const category = String(record.service_category ?? '');
  for (const known of spec.category_vocab) row[`cat::${known}`] = category === known ? 1 : 0;

  const deadline = String(record.deadline ?? '');
  for (const known of spec.deadline_vocab) row[`deadline::${known}`] = deadline === known ? 1 : 0;

  return row;
}

export function buildVector(record, spec) {
  const row = buildFeatureRow(record, spec);
  return featureOrder(spec).map((name) => row[name]);
}
