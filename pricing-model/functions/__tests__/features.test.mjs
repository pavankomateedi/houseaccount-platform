// Feature parity: the JS builder must reproduce Python's vectors exactly,
// otherwise the model.json coefficients are applied to the wrong inputs.
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';

import { baselineMidpoint, buildVector, extractScope, normalizeCategory } from '../_lib/features.js';

const model = JSON.parse(readFileSync(new URL('./fixtures/model.json', import.meta.url)));
const parity = JSON.parse(readFileSync(new URL('./fixtures/feature_parity.json', import.meta.url)));

test('normalizeCategory mirrors Python normalize_category', () => {
  assert.equal(normalizeCategory('plumbing'), 'Plumbing');
  assert.equal(normalizeCategory('PLUMBING'), 'Plumbing');
  assert.equal(normalizeCategory('pest-control'), 'Pest Control');
  assert.equal(normalizeCategory('hvac'), 'HVAC');
  assert.equal(normalizeCategory('  General Contractor '), 'General Contractor');
});

test('extractScope counts words, largest number, and materials flag', () => {
  const scope = extractScope('Exterior window wash, 2-story, 20 windows');
  assert.equal(scope.desc_word_count, 6);
  assert.equal(scope.max_number, 20);
  assert.equal(extractScope('Replace valve, you supply valve').materials_supplied, 1);
  assert.equal(extractScope('Replace valve').materials_supplied, 0);
});

test('request-style original_estimate_lo/hi feed the baseline midpoint', () => {
  const midpoint = baselineMidpoint(
    { original_estimate_lo: 100, original_estimate_hi: 300 },
    model.spec,
  );
  assert.equal(midpoint, 200);
});

parity.cases.forEach((parityCase, index) => {
  test(`feature parity case ${index}`, () => {
    const vector = buildVector(parityCase.record, model.spec);
    assert.equal(vector.length, parityCase.vector.length);
    for (let j = 0; j < vector.length; j += 1) {
      assert.ok(
        Math.abs(vector[j] - parityCase.vector[j]) < 1e-9,
        `feature ${model.feature_order[j]}: js=${vector[j]} py=${parityCase.vector[j]}`,
      );
    }
  });
});
