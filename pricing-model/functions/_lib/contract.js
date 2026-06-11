// HTTP contract helpers: bearer auth, required-field validation, JSON responses.
// Mirrors the conventions in receive-homeowner.js (Appendix A sources).

import { timingSafeEqual } from 'node:crypto';

export const REQUIRED_FIELDS = ['job_id', 'service_category', 'zip_code', 'job_description'];

// Constant-time bearer comparison against the shared secret.
export function validateBearer(authHeader, secret) {
  const authz = authHeader || '';
  if (!authz.startsWith('Bearer ')) return false;
  const presented = Buffer.from(authz.slice('Bearer '.length));
  const expected = Buffer.from(secret || '');
  return presented.length === expected.length && timingSafeEqual(presented, expected);
}

// First missing/blank required field, or null when all present.
export function firstMissingField(body) {
  for (const field of REQUIRED_FIELDS) {
    const value = body[field];
    if (value === undefined || value === null || value === '') return field;
  }
  return null;
}

export function jsonResponse(status, payload) {
  return new Response(JSON.stringify(payload), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
}
