// The clarifying-questions logic is product UX; pin its behavior.
import assert from 'node:assert/strict';
import test from 'node:test';

import { clarifyingGuidance } from '../_lib/clarify.js';

const confident = { confidence: 0.82 };
const lowConfidence = { confidence: 0.3 };

test('asks category-specific questions for a known category', () => {
  const { questions } = clarifyingGuidance(
    { service_category: 'Plumbing', job_description: 'Replace 3 plumbing fixtures, you supply materials', original_estimate: 360 },
    confident,
  );
  assert.ok(questions.some((q) => /repair or a full replacement/i.test(q)));
});

test('falls back to generic questions for an unknown category', () => {
  const { questions } = clarifyingGuidance(
    { service_category: 'Underwater Basket Weaving', job_description: 'Weave a basket underwater', original_estimate: 200 },
    confident,
  );
  assert.ok(questions.some((q) => /size or quantity/i.test(q)));
});

test('asks for more detail when the description is thin', () => {
  const { questions } = clarifyingGuidance(
    { service_category: 'Cleaning', job_description: 'clean', original_estimate: 200 },
    confident,
  );
  assert.ok(questions[0].includes('describe the job in more detail'));
});

test('requests a prior quote when no estimate is supplied', () => {
  const { questions } = clarifyingGuidance(
    { service_category: 'Handyman', job_description: 'Mount a TV and hang two shelves in the den' },
    confident,
  );
  assert.ok(questions.some((q) => /prior quote/i.test(q)));
});

test('explains specialist routing when confidence is low', () => {
  const { note } = clarifyingGuidance(
    { service_category: 'Roofing', job_description: 'Full roof replacement, 1800 sqft', original_estimate: 9000 },
    lowConfidence,
  );
  assert.ok(note && /specialist/i.test(note));
});

test('caps the number of questions', () => {
  const { questions } = clarifyingGuidance(
    { service_category: 'Plumbing', job_description: 'x' },
    confident,
  );
  assert.ok(questions.length <= 4);
});
