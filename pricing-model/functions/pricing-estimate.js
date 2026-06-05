import { timingSafeEqual } from 'node:crypto';

const GAUNTLET_PRICING_SECRET = process.env.GAUNTLET_PRICING_SECRET || '';

if (!GAUNTLET_PRICING_SECRET) {
  throw new Error('GAUNTLET_PRICING_SECRET env var is required');
}

/**
 * Validate Bearer token authorization
 */
function validateBearer(req) {
  const authz = req.headers.get('authorization') || '';
  if (!authz.startsWith('Bearer ')) return false;

  const presented = Buffer.from(authz.slice('Bearer '.length));
  const expected = Buffer.from(GAUNTLET_PRICING_SECRET || '');

  return (
    presented.length === expected.length &&
    timingSafeEqual(presented, expected)
  );
}

/**
 * Validate request schema
 */
function validateRequest(body) {
  const required = ['job_id', 'service_category', 'zip_code', 'job_description'];

  for (const field of required) {
    if (!body[field]) {
      return { valid: false, error: `${field} required` };
    }
  }

  return { valid: true };
}

/**
 * Netlify Function: POST /.netlify/functions/pricing-estimate
 */
export default async (req, context) => {
  // Method check
  if (req.method !== 'POST') {
    return new Response(
      JSON.stringify({ error: 'Method not allowed' }),
      { status: 405, headers: { 'Content-Type': 'application/json' } }
    );
  }

  // Auth check
  if (!validateBearer(req)) {
    return new Response(
      JSON.stringify({ error: 'Unauthorized' }),
      { status: 401, headers: { 'Content-Type': 'application/json' } }
    );
  }

  // Parse JSON body
  let body;
  try {
    body = await req.json();
  } catch (e) {
    return new Response(
      JSON.stringify({ error: 'Malformed JSON' }),
      { status: 400, headers: { 'Content-Type': 'application/json' } }
    );
  }

  // Validate schema
  const validation = validateRequest(body);
  if (!validation.valid) {
    return new Response(
      JSON.stringify({ error: validation.error }),
      { status: 400, headers: { 'Content-Type': 'application/json' } }
    );
  }

  // Generate estimate (mock for now - in production would call Python inference)
  try {
    const estimate = generateEstimate(body);

    return new Response(
      JSON.stringify(estimate),
      { status: 200, headers: { 'Content-Type': 'application/json' } }
    );
  } catch (error) {
    return new Response(
      JSON.stringify({ error: error.message || 'Internal error' }),
      { status: 500, headers: { 'Content-Type': 'application/json' } }
    );
  }
};

/**
 * Generate pricing estimate from request
 * In production, this would call the Python inference server
 */
function generateEstimate(request) {
  const originalEst = request.original_estimate || 1000;
  const interval = (request.original_estimate_hi || 1500) -
                   (request.original_estimate_lo || 500);

  // Simplified prediction
  const midpoint = originalEst * (0.95 + Math.random() * 0.1);
  const lo = Math.max(midpoint - interval / 2, 0);
  const hi = midpoint + interval / 2;

  // Confidence calibration
  let confidence = 0.75;

  const productionCategories = new Set([
    'electrical', 'exterior', 'handyman', 'hvac', 'cleaning',
    'landscaping', 'pest-control', 'plumbing'
  ]);

  if (!productionCategories.has(request.service_category.toLowerCase())) {
    confidence *= 0.65;
  }

  if (midpoint > 5000) {
    confidence *= 0.65;
  }

  if (interval > 3000) {
    confidence *= 0.75;
  }

  return {
    ok: true,
    job_id: request.job_id,
    estimate_lo: Math.round(lo * 100) / 100,
    estimate_hi: Math.round(hi * 100) / 100,
    estimate_midpoint: Math.round(midpoint * 100) / 100,
    confidence: Math.max(0, Math.min(1, confidence)),
    model_version: 'pavan-v1.0.0'
  };
}
