import assert from 'node:assert/strict'
import test from 'node:test'
import { attemptApi } from '../src/challenge/dataAccessInterface/attemptGatewayApi.ts'

const challenge = {
  name: 'Forgot Password x3',
  slug: 'forgot-password-x3',
  challenge_date: '2026-11-18',
  difficulty: 1,
  category: 'account',
}

const turn = (id, type) => ({
  id,
  type,
  transcript_url: `media/${id}.txt`,
  audio_url: `media/${id}.mp3`,
})

const rawSnapshot = (overrides = {}) => ({
  attempt_id: '627e5d91-c343-44ae-b6ab-532b2ed41b8e',
  stage: 'tone',
  challenge,
  opening: turn('c1', 'question'),
  conversation: [],
  choices: [],
  tone_correct: null,
  tone_time: null,
  tone_speed_correct: null,
  ...overrides,
})

const transcript = (text) =>
  new Response(text, { headers: { 'content-type': 'text/plain' } })

function mockBrowser(t) {
  const originalWindow = globalThis.window
  globalThis.window = {
    location: { origin: 'http://localhost:5173' },
  }
  t.after(() => {
    globalThis.window = originalWindow
  })
}

function mockFetch(t, handler) {
  t.mock.method(globalThis, 'fetch', handler)
}

const csrf = () => Response.json({ csrfToken: 'fresh-token' })

function assertCsrfRequest(url, options, signal) {
  assert.equal(url, '/api/users/auth/csrf/')
  assert.equal(options.credentials, 'same-origin')
  assert.equal(options.cache, 'no-store')
  assert.equal(options.signal, signal)
}

function assertPost(options, signal) {
  assert.equal(options.method, 'POST')
  assert.equal(options.credentials, 'same-origin')
  assert.equal(options.signal, signal)
  assert.equal(options.headers['Content-Type'], 'application/json')
  assert.equal(options.headers['X-CSRFToken'], 'fresh-token')
}

test('starting a challenge posts an empty object and hydrates the opening', async (t) => {
  mockBrowser(t)
  const signal = new AbortController().signal
  mockFetch(t, async (url, options) => {
    if (url === '/api/users/auth/csrf/') {
      assertCsrfRequest(url, options, signal)
      return csrf()
    }
    if (url === '/api/challenges/forgot-password-x3/attempts/') {
      assertPost(options, signal)
      assert.equal(options.body, '{}')
      return Response.json(rawSnapshot(), { status: 201 })
    }
    if (url === 'http://localhost:5173/media/c1.txt') {
      assert.equal(options.signal, signal)
      return transcript(' Customer opening\n')
    }
    throw new Error(`Unexpected request: ${url}`)
  })
  const snapshot = await attemptApi.start('forgot-password-x3', signal)
  assert.equal(snapshot.attemptId, '627e5d91-c343-44ae-b6ab-532b2ed41b8e')
  assert.equal(snapshot.stage, 'tone')
  assert.deepEqual(snapshot.opening, {
    id: 'c1',
    type: 'question',
    transcriptUrl: 'http://localhost:5173/media/c1.txt',
    audioUrl: 'http://localhost:5173/media/c1.mp3',
    text: 'Customer opening',
  })
  assert.deepEqual(snapshot.conversation, [])
  assert.deepEqual(snapshot.choices, [])
})

test('tone submission sends only the answer and maps the conversation snapshot', async (t) => {
  mockBrowser(t)
  const signal = new AbortController().signal
  mockFetch(t, async (url, options) => {
    if (url === '/api/users/auth/csrf/') return csrf()
    if (url === '/api/attempts/attempt-1/tone/') {
      assertPost(options, signal)
      assert.equal(options.body, JSON.stringify({ answer: 'calm' }))
      return Response.json(
        rawSnapshot({
          stage: 'conversation',
          conversation: [turn('c1', 'question')],
          choices: [{ ...turn('a1', 'response'), choice_id: '0' }],
          tone_correct: true,
          tone_time: 4.2,
          tone_speed_correct: true,
          tone_similarity: 0.8,
        }),
      )
    }
    if (url === 'http://localhost:5173/media/c1.txt') {
      return transcript('Customer opening')
    }
    if (url === 'http://localhost:5173/media/a1.txt') {
      return transcript('Agent reply')
    }
    throw new Error(`Unexpected request: ${url}`)
  })
  const snapshot = await attemptApi.submitTone('attempt-1', 'calm', signal)
  assert.equal(snapshot.stage, 'conversation')
  assert.equal(snapshot.toneCorrect, true)
  assert.equal(snapshot.toneTime, 4.2)
  assert.equal(snapshot.toneSpeedCorrect, true)
  assert.equal(snapshot.toneSimilarity, 0.8)
  assert.deepEqual(
    snapshot.conversation.map(({ id }) => id),
    ['c1'],
  )
  assert.deepEqual(snapshot.choices, [
    {
      id: 'a1',
      type: 'response',
      transcriptUrl: 'http://localhost:5173/media/a1.txt',
      audioUrl: 'http://localhost:5173/media/a1.mp3',
      text: 'Agent reply',
      choiceId: '0',
    },
  ])
})

test('choice, continue, action, and load use their documented endpoints', async (t) => {
  mockBrowser(t)
  const signal = new AbortController().signal
  const calls = []
  mockFetch(t, async (url, options) => {
    if (url === '/api/users/auth/csrf/') return csrf()
    if (url === 'http://localhost:5173/media/c1.txt') {
      return transcript('Opening')
    }
    if (url === 'http://localhost:5173/media/a1.txt') {
      return transcript('Reply')
    }
    if (url === '/api/attempts/attempt-1/choices/') {
      assertPost(options, signal)
      assert.equal(options.body, JSON.stringify({ choice_id: '0' }))
      calls.push('choices')
      return Response.json(
        rawSnapshot({
          stage: 'conversation',
          conversation: [turn('c1', 'question'), turn('a1', 'response')],
          choices: [],
        }),
      )
    }
    if (url === '/api/attempts/attempt-1/continue/') {
      assertPost(options, signal)
      assert.equal(options.body, '{}')
      calls.push('continue')
      return Response.json(
        rawSnapshot({
          stage: 'action',
          conversation: [turn('c1', 'question'), turn('a1', 'response')],
        }),
      )
    }
    if (url === '/api/attempts/attempt-1/action/') {
      assertPost(options, signal)
      assert.equal(options.body, JSON.stringify({ answer: 'reset password' }))
      calls.push('action')
      return Response.json(
        rawSnapshot({
          stage: 'completed',
          conversation: [turn('c1', 'question'), turn('a1', 'response')],
          tone_correct: true,
          tone_time: 4,
          tone_speed_correct: true,
          action_correct: true,
          score: 3,
          required_action: 'reset password',
          completed_at: '2026-11-11T12:00:00+00:00',
        }),
      )
    }
    if (url === '/api/attempts/attempt-1/') {
      assert.equal(options.method, undefined)
      assert.equal(options.signal, signal)
      calls.push('load')
      return Response.json(
        rawSnapshot({
          stage: 'action',
          conversation: [turn('c1', 'question'), turn('a1', 'response')],
          tone_correct: true,
          tone_time: 4,
          tone_speed_correct: true,
        }),
      )
    }
    throw new Error(`Unexpected request: ${url}`)
  })

  const chosen = await attemptApi.chooseResponse('attempt-1', '0', signal)
  assert.deepEqual(
    chosen.conversation.map(({ id }) => id),
    ['c1', 'a1'],
  )

  const continued = await attemptApi.continueConversation('attempt-1', signal)
  assert.equal(continued.stage, 'action')

  const completed = await attemptApi.submitAction(
    'attempt-1',
    'reset password',
    signal,
  )
  assert.equal(completed.actionCorrect, true)
  assert.equal(completed.score, 3)
  assert.equal(completed.requiredAction, 'reset password')
  assert.equal(completed.completedAt, '2026-11-11T12:00:00+00:00')

  const loaded = await attemptApi.load('attempt-1', signal)
  assert.equal(loaded.stage, 'action')
  assert.deepEqual(calls, ['choices', 'continue', 'action', 'load'])
})

test('404 and 403 loads are treated as stale stored attempts', async (t) => {
  mockBrowser(t)
  for (const status of [404, 403]) {
    t.mock.method(globalThis, 'fetch', async () =>
      Response.json({ detail: 'Unavailable.' }, { status }),
    )
    assert.equal(
      await attemptApi.load('attempt-1', new AbortController().signal),
      null,
    )
  }
})

test('tone failures map to retryable user-facing messages', async (t) => {
  mockBrowser(t)
  mockFetch(t, async (url) => {
    if (url === '/api/users/auth/csrf/') return csrf()
    return Response.json({ detail: 'Unknown tone answer.' }, { status: 404 })
  })
  await assert.rejects(
    attemptApi.submitTone('attempt-1', 'calm', new AbortController().signal),
    /Tone not recognized. Try another word or phrase./,
  )
})

test('missing transcripts reject instead of rendering fake text', async (t) => {
  mockBrowser(t)
  mockFetch(t, async (url) => {
    if (url === '/api/users/auth/csrf/') return csrf()
    if (url === '/api/challenges/forgot-password-x3/attempts/') {
      return Response.json(rawSnapshot())
    }
    return new Response('<html>App shell</html>', {
      headers: { 'content-type': 'text/html' },
    })
  })
  await assert.rejects(
    attemptApi.start('forgot-password-x3', new AbortController().signal),
    /transcript is missing/,
  )
})
