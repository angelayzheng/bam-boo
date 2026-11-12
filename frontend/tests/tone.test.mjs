import assert from 'node:assert/strict'
import test from 'node:test'
import { scoreTone } from '../src/dataAccessInterface/toneGatewayApi.ts'

test('sends only the answer and challenge slug with the cancellation signal', async (t) => {
  const controller = new AbortController()
  t.mock.method(globalThis, 'fetch', async (url, { signal }) => {
    assert.equal(url, '/api/tone/calm-challenge/?answer=very%20calm')
    assert.equal(signal, controller.signal)
    return Response.json({ similarity: 0.8, correct: true })
  })
  assert.equal(
    await scoreTone(' very calm ', 'calm-challenge', controller.signal),
    true,
  )
})

test('uses the backend correctness decision', async (t) => {
  for (const correct of [true, false]) {
    t.mock.method(globalThis, 'fetch', async () =>
      Response.json({ similarity: 0.6, correct }),
    )
    assert.equal(
      await scoreTone('calm', 'calm-challenge', new AbortController().signal),
      correct,
    )
  }
})

test('unknown tones, missing challenges and service failures are retryable errors', async (t) => {
  for (const status of [404, 503, 500]) {
    t.mock.method(globalThis, 'fetch', async () => new Response('', { status }))
    await assert.rejects(
      scoreTone('unknown', 'calm-challenge', new AbortController().signal),
      status === 404 ? /not recognized/ : /unavailable/,
    )
  }
})

test('rejects missing or invalid scores and correctness decisions', async (t) => {
  for (const result of [
    {},
    { similarity: null, correct: true },
    { similarity: '0.9', correct: true },
    { similarity: 2, correct: true },
    { similarity: -2, correct: true },
    { similarity: 0.8 },
    { similarity: 0.8, correct: 'true' },
  ]) {
    t.mock.method(globalThis, 'fetch', async () => Response.json(result))
    await assert.rejects(
      scoreTone('calm', 'calm-challenge', new AbortController().signal),
      /invalid score/,
    )
  }
})

test('network and cancellation failures propagate', async (t) => {
  const failure = new DOMException('Cancelled', 'AbortError')
  t.mock.method(globalThis, 'fetch', async () => {
    throw failure
  })
  await assert.rejects(
    scoreTone('calm', 'calm-challenge', new AbortController().signal),
    (error) => error === failure,
  )
})
