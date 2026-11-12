import assert from 'node:assert/strict'
import test from 'node:test'
import {
  loadByDate,
  loadChallengeSummaries,
  loadDetail,
} from '../src/dataAccessInterface/challengeGatewayApi.ts'

const root = {
  type: 'question',
  node_key: 'c1',
  transcript_url: 'media/c1.txt',
  audio_url: 'media/c1.mp3',
  children: [
    {
      type: 'response',
      node_key: 'a1',
      transcript_url: 'media/a1.txt',
      audio_url: 'media/a1.mp3',
      children: [],
    },
  ],
}
const demo = {
  name: 'Forgot Password x3',
  slug: 'forgot-password-x3',
  challenge_date: '2026-10-15',
  difficulty: 1,
  category: 'account',
  required_action: 'reset password',
  conversation_tree: root,
}

function mockBackend(t, handler) {
  t.mock.method(globalThis, 'fetch', handler)
  const originalWindow = globalThis.window
  globalThis.window = { location: { origin: 'http://localhost:5173' } }
  t.after(() => {
    globalThis.window = originalWindow
  })
}

test('summaries load from the challenge list', async (t) => {
  mockBackend(t, async (url, { signal }) => {
    assert.ok(signal instanceof AbortSignal)
    if (url === '/api/challenges/') return Response.json({ challenges: [demo] })
    throw new Error(`Unexpected request: ${url}`)
  })
  const summaries = await loadChallengeSummaries(new AbortController().signal)
  assert.equal(summaries.length, 1)
  assert.equal(summaries[0].slug, 'forgot-password-x3')
})

test('detail loads and hydrates transcript and media URLs from any page route', async (t) => {
  mockBackend(t, async (url, { signal }) => {
    assert.ok(signal instanceof AbortSignal)
    if (url === '/api/challenges/forgot-password-x3/')
      return Response.json(demo)
    if (url === 'http://localhost:5173/media/c1.txt')
      return new Response(' Customer opening\n')
    if (url === 'http://localhost:5173/media/a1.txt')
      return new Response('Agent reply\n')
    throw new Error(`Unexpected request: ${url}`)
  })
  const challenge = await loadDetail(
    'forgot-password-x3',
    new AbortController().signal,
  )
  assert.equal(challenge.slug, 'forgot-password-x3')
  assert.equal(challenge.conversation_tree.text, 'Customer opening')
  assert.equal(
    challenge.conversation_tree.audio_url,
    'http://localhost:5173/media/c1.mp3',
  )
  assert.equal(challenge.conversation_tree.children[0].text, 'Agent reply')
})

test('loading by date finds the summary and hydrates its detail', async (t) => {
  mockBackend(t, async (url) => {
    if (url === '/api/challenges/') return Response.json({ challenges: [demo] })
    if (url === '/api/challenges/forgot-password-x3/')
      return Response.json(demo)
    if (url === 'http://localhost:5173/media/c1.txt')
      return new Response('Customer opening\n')
    if (url === 'http://localhost:5173/media/a1.txt')
      return new Response('Agent reply\n')
    throw new Error(`Unexpected request: ${url}`)
  })
  const challenge = await loadByDate('2026-10-15', new AbortController().signal)
  assert.equal(challenge.slug, 'forgot-password-x3')
})

test('an unknown date gives an actionable error', async (t) => {
  mockBackend(t, async () => Response.json({ challenges: [] }))
  await assert.rejects(
    loadByDate('2026-10-15', new AbortController().signal),
    /No recordings are available/,
  )
})

test('a backend error does not render a fake scenario', async (t) => {
  mockBackend(t, async () => new Response('Error', { status: 500 }))
  await assert.rejects(
    loadByDate('2026-10-15', new AbortController().signal),
    /Django backend/,
  )
})

test('a missing transcript does not get mistaken for the Vite HTML fallback', async (t) => {
  mockBackend(t, async (url) => {
    if (url === '/api/challenges/') return Response.json({ challenges: [demo] })
    if (url === '/api/challenges/forgot-password-x3/')
      return Response.json(demo)
    return new Response('<html>App shell</html>', {
      headers: { 'content-type': 'text/html' },
    })
  })
  await assert.rejects(
    loadDetail('forgot-password-x3', new AbortController().signal),
    /transcript is missing/,
  )
})
