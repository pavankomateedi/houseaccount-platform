// JS calibration must agree with the same golden cases the Python side uses.
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';

import { calibrateConfidence, oodFlags } from '../_lib/calibration.js';

const golden = JSON.parse(
  readFileSync(new URL('../../eval/goldenset/calibration_cases.json', import.meta.url)),
);
const medianInterval = golden.median_interval;

for (const testCase of golden.cases) {
  test(`calibration: ${testCase.name}`, () => {
    const { midpoint, lo, hi, category, expect } = testCase;
    const confidence = calibrateConfidence(midpoint, lo, hi, category, medianInterval);

    if (expect.confidence_min !== undefined) {
      assert.ok(confidence >= expect.confidence_min, `confidence ${confidence}`);
    }
    if (expect.confidence_max !== undefined) {
      assert.ok(confidence <= expect.confidence_max, `confidence ${confidence}`);
    }
    if (expect.flags) {
      const flags = oodFlags(midpoint, lo, hi, category, medianInterval);
      for (const [axis, value] of Object.entries(expect.flags)) {
        assert.equal(flags[axis], value, axis);
      }
    }
  });
}
