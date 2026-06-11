// POST /.netlify/functions/pricing-estimate
// Booking input in, model-backed price estimate + confidence out (Appendix A).
//
// Presentation layer only: method/auth/validation, then delegate to the model
// (functions/_lib/infer.js) which evaluates the exported model.json.

import { firstMissingField, jsonResponse, validateBearer } from './_lib/contract.js';
import { predict } from './_lib/infer.js';

const GAUNTLET_PRICING_SECRET = process.env.GAUNTLET_PRICING_SECRET || '';

// Boot-time enforcement: fail fast on cold start if the secret is unset
// (matches receive-homeowner.js:20-22).
if (!GAUNTLET_PRICING_SECRET) {
  throw new Error('GAUNTLET_PRICING_SECRET env var is required');
}

export default async (req) => {
  if (req.method !== 'POST') {
    return jsonResponse(405, { error: 'Method not allowed' });
  }

  if (!validateBearer(req.headers.get('authorization'), GAUNTLET_PRICING_SECRET)) {
    return jsonResponse(401, { error: 'Unauthorized' });
  }

  let body;
  try {
    body = await req.json();
  } catch {
    return jsonResponse(400, { error: 'Malformed JSON' });
  }

  const missing = firstMissingField(body);
  if (missing) {
    return jsonResponse(400, { error: `${missing} required` });
  }

  try {
    const estimate = predict(body);
    return jsonResponse(200, { ok: true, job_id: body.job_id, ...estimate });
  } catch {
    return jsonResponse(500, { error: 'Estimate failed' });
  }
};
