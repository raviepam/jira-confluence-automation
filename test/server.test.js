import test from 'node:test';
import assert from 'node:assert/strict';
import { createApp } from '../server.js';

const app = createApp();

test('GET /api/health returns status ok', async () => {
  const response = await fetch('http://localhost:3000/api/health', {
    method: 'GET'
  }).catch(() => null);

  if (response) {
    assert.equal(response.status, 200);
    const json = await response.json();
    assert.deepEqual(json, { status: 'ok' });
    return;
  }

  const server = app.listen(3000);
  try {
    const res = await fetch('http://localhost:3000/api/health');
    assert.equal(res.status, 200);
    const json = await res.json();
    assert.deepEqual(json, { status: 'ok' });
  } finally {
    await new Promise((resolve) => server.close(resolve));
  }
});

test('POST /api/chat returns a helpful fallback response', async () => {
  const server = app.listen(3001);
  try {
    const res = await fetch('http://localhost:3001/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt: 'Say hello' })
    });

    assert.equal(res.status, 200);
    const json = await res.json();
    assert.match(json.message, /hello|Hello|Hi/i);
  } finally {
    await new Promise((resolve) => server.close(resolve));
  }
});
