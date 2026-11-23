import assert from 'node:assert/strict'
import test from 'node:test'
import { loadChallengeSummaries } from '../src/challenge/dataAccessInterface/challengeGatewayApi.ts'

const demo = {
  name: 'Forgot Password x3',
  slug: 'forgot-password-x3',
  challenge_date: '2026-10-15',
  difficulty: 1,
  category: 'account',
}

test('summaries load from the challenge list', async (t) => {
  const signal = new AbortController().signal
  t.mock.method(globalThis, 'fetch', async (url, options) => {
    assert.equal(url, '/api/challenges/')
    assert.equal(options.credentials, 'same-origin')
    assert.equal(options.cache, 'no-store')
    assert.equal(options.signal, signal)
    return Response.json({ challenges: [demo] })
  })
  const summaries = await loadChallengeSummaries(signal)
  assert.equal(summaries.length, 1)
  assert.equal(summaries[0].slug, 'forgot-password-x3')
})

test('a backend failure surfaces as a load error', async (t) => {
  t.mock.method(
    globalThis,
    'fetch',
    async () => new Response('Error', { status: 500 }),
  )
  await assert.rejects(
    loadChallengeSummaries(new AbortController().signal),
    /Django backend/,
  )
})
