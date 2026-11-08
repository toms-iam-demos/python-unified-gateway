'use strict';

// Synthetic fixtures only; no DOM, database, network, or provider access.
const assert = require('node:assert/strict');
const { test } = require('node:test');
const { redact } = require('../gateway/event_explorer/app.js');

const token = 'SYNTHETIC_TOKEN_ONLY';
const completeBody = JSON.stringify({
  event: 'synthetic-masking-regression',
  token,
  email: 'synthetic@example.invalid',
  padding: 'x'.repeat(8000),
});
// Reproduce the event-browser snapshot's 4,000-byte raw-body preview.
const truncatedBody = Buffer.from(completeBody, 'utf8').subarray(0, 4000).toString('utf8');

for (const personalMasking of [true, false]) {
  test(`complete JSON redacts credentials with personal masking ${personalMasking}`, () => {
    const rendered = redact(completeBody, personalMasking);
    assert.equal(rendered.includes(token), false);
    assert.ok(rendered.includes('[redacted]'));
    assert.equal(JSON.parse(completeBody).token, token, 'Stored source must stay unchanged');
  });

  test(`truncated raw JSON redacts credentials with personal masking ${personalMasking}`, () => {
    assert.equal(Buffer.byteLength(truncatedBody, 'utf8'), 4000);
    assert.throws(() => JSON.parse(truncatedBody), SyntaxError);
    assert.ok(truncatedBody.includes(token), 'Fixture must include the complete synthetic token');
    const rendered = redact(truncatedBody, personalMasking);
    assert.equal(
      rendered.includes(token),
      false,
      'Truncated raw preview must not expose credentials, regardless of personal masking',
    );
    assert.ok(rendered.includes('[redacted]'));
  });
}

for (const key of ['access_token', 'Authorization', 'credentials', 'api_key', 'pass\\u0077ord']) {
  test(`incomplete credential preview is hidden for ${key}`, () => {
    const preview = '{"' + key + '":"SYNTHETIC_CREDENTIAL_ONLY","padding":"unfinished';
    for (const personal of [true, false]) {
      const rendered = redact(preview, personal);
      assert.equal(rendered.includes('SYNTHETIC_CREDENTIAL_ONLY'), false);
      assert.ok(rendered.includes('[redacted]'));
    }
  });
}

test('incomplete nested credential values are hidden', () => {
  const rendered = redact('{"credentials":{"first":"SYNTHETIC_ONE","second":"SYNTHETIC_TWO",');
  assert.equal(rendered.includes('SYNTHETIC_'), false);
});

test('noncredential raw previews and plaintext masking keep existing behavior', () => {
  const raw = '{"event":"synthetic","padding":"unfinished';
  assert.equal(redact(raw, false), raw);
  assert.equal(redact('Bearer SYNTHETIC_ONLY', false), 'Bearer [redacted]');
  assert.equal(redact('synthetic@example.invalid', true), '[email masked]');
  assert.equal(redact('synthetic@example.invalid', false), 'synthetic@example.invalid');
});

test('malformed key escapes fail closed without breaking the viewer', () => {
  const rendered = redact('{"bad\\qkey":"synthetic","token":"SYNTHETIC_ONLY",');
  assert.ok(rendered.includes('[redacted]'));
  assert.equal(rendered.includes('SYNTHETIC_ONLY'), false);
});
