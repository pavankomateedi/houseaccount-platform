// HTTP contract conformance: drive the real handler with the golden cases.
// Env must be set before importing the handler (it enforces the secret at boot
// and reads the model path), so this file imports it dynamically.
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import test from 'node:test';

const SECRET = 'test-secret';
process.env.GAUNTLET_PRICING_SECRET = SECRET;
process.env.PRICING_MODEL_PATH = fileURLToPath(new URL('./fixtures/model.json', import.meta.url));

const { default: handler } = await import('../pricing-estimate.js');
const golden = JSON.parse(
  readFileSync(new URL('../../eval/goldenset/contract_cases.json', import.meta.url)),
);
const edge = JSON.parse(
  readFileSync(new URL('../../eval/goldenset/edge_request_cases.json', import.meta.url)),
);

const ENDPOINT = 'http://localhost/.netlify/functions/pricing-estimate';

function buildBody(testCase) {
  if (testCase.raw_body !== undefined) return testCase.raw_body;
  const body = { ...golden.valid_body };
  if (testCase.omit) delete body[testCase.omit];
  if (testCase.override) Object.assign(body, testCase.override);
  return JSON.stringify(body);
}

function authHeader(kind) {
  if (kind === 'valid') return `Bearer ${SECRET}`;
  if (kind === 'wrong') return 'Bearer wrong-secret';
  return undefined;
}

function makeRequest(testCase) {
  const headers = { 'Content-Type': 'application/json' };
  const auth = authHeader(testCase.auth);
  if (auth) headers.Authorization = auth;
  const init = { method: testCase.method, headers };
  if (testCase.method !== 'GET' && testCase.method !== 'HEAD') {
    init.body = buildBody(testCase);
  }
  return new Request(ENDPOINT, init);
}

// Behavioral check of schema/response.schema.json (additionalProperties: false).
function assertResponseShape(json) {
  assert.deepEqual(
    Object.keys(json).sort(),
    ['confidence', 'estimate_hi', 'estimate_lo', 'estimate_midpoint', 'job_id', 'model_version', 'ok'],
  );
  assert.equal(json.ok, true);
  assert.equal(typeof json.job_id, 'string');
  assert.ok(json.estimate_lo >= 0);
  assert.ok(json.estimate_lo <= json.estimate_midpoint);
  assert.ok(json.estimate_midpoint <= json.estimate_hi);
  assert.ok(json.confidence >= 0 && json.confidence <= 1);
  assert.ok(typeof json.model_version === 'string' && json.model_version.length > 0);
}

for (const testCase of golden.cases) {
  test(`contract: ${testCase.name}`, async () => {
    const response = await handler(makeRequest(testCase));
    assert.equal(response.status, testCase.expect.status);

    const json = await response.json();
    const { expect } = testCase;
    if (expect.error !== undefined) assert.equal(json.error, expect.error);
    if (expect.ok !== undefined) assert.equal(json.ok, expect.ok);
    if (expect.echo_job_id) assert.equal(json.job_id, expect.echo_job_id);
    if (expect.schema === 'response') assertResponseShape(json);
  });
}

// End-to-end robustness / OOD pass-through (all with valid auth).
function edgeRequest(body) {
  return new Request(ENDPOINT, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${SECRET}` },
    body: JSON.stringify(body),
  });
}

for (const testCase of edge.cases) {
  test(`edge: ${testCase.name}`, async () => {
    const response = await handler(edgeRequest(testCase.body));
    assert.equal(response.status, testCase.expect.status);

    const json = await response.json();
    const { expect } = testCase;
    if (expect.ok !== undefined) assert.equal(json.ok, expect.ok);
    if (expect.valid_shape) assertResponseShape(json);
    if (expect.confidence_max !== undefined) {
      assert.ok(json.confidence <= expect.confidence_max, `confidence ${json.confidence}`);
    }
    if (expect.confidence_min !== undefined) {
      assert.ok(json.confidence >= expect.confidence_min, `confidence ${json.confidence}`);
    }
  });
}
