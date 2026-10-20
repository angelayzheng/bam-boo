import assert from 'node:assert/strict'
import test from 'node:test'
import { loadChallenge } from '../src/challenges.ts'

const root = {
  type: 'question',
  text_file: 'c1.txt',
  audio_file: 'c1.mp3',
  transcript_url: 'media/c1.txt',
  audio_url: 'media/c1.mp3',
  children: [
    {
      type: 'response',
      text_file: 'a1.txt',
      audio_file: 'a1.mp3',
      transcript_url: 'media/a1.txt',
      audio_url: 'media/a1.mp3',
      children: [],
    },
  ],
}
const demo = {
  id: 42,
  name: 'Forgot Password x3',
  slug: 'forgot-password-x3',
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

test('loads the existing demo and hydrates transcript and media URLs from any page route', async (t) => {
  mockBackend(t, async (url, { signal }) => {
    assert.ok(signal instanceof AbortSignal)
    if (url === '/api/challenges/')
      return Response.json({
        challenges: [{ id: 1, slug: 'unrecorded' }, demo],
      })
    if (url === '/api/challenges/42/') return Response.json(demo)
    if (url === 'http://localhost:5173/media/c1.txt')
      return new Response(' Customer opening\n')
    if (url === 'http://localhost:5173/media/a1.txt')
      return new Response('Agent reply\n')
    throw new Error(`Unexpected request: ${url}`)
  })
  const challenge = await loadChallenge(new AbortController().signal)
  assert.equal(challenge.id, 42)
  assert.equal(challenge.conversation_tree.text, 'Customer opening')
  assert.equal(
    challenge.conversation_tree.audio_url,
    'http://localhost:5173/media/c1.mp3',
  )
  assert.equal(challenge.conversation_tree.children[0].text, 'Agent reply')
})

test('an empty database gives an actionable error', async (t) => {
  mockBackend(t, async () => Response.json({ challenges: [] }))
  await assert.rejects(
    loadChallenge(new AbortController().signal),
    /No recordings are available/,
  )
})

test('a backend error does not render a fake scenario', async (t) => {
  mockBackend(t, async () => new Response('Error', { status: 500 }))
  await assert.rejects(
    loadChallenge(new AbortController().signal),
    /Django backend/,
  )
})

test('a missing transcript does not get mistaken for the Vite HTML fallback', async (t) => {
  mockBackend(t, async (url) => {
    if (url === '/api/challenges/') return Response.json({ challenges: [demo] })
    if (url === '/api/challenges/42/') return Response.json(demo)
    return new Response('<html>App shell</html>', {
      headers: { 'content-type': 'text/html' },
    })
  })
  await assert.rejects(
    loadChallenge(new AbortController().signal),
    /transcript is missing/,
  )
})
