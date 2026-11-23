import assert from 'node:assert/strict'
import test from 'node:test'
import { resultClaimApi } from '../src/results/dataAccessInterface/resultClaimGatewayApi.ts'
import { ResultClaimError } from '../src/results/boundaries/dataAccessInterfaces.ts'

const basePath = '/api/users/auth/'
const attemptId = '627e5d91-c343-44ae-b6ab-532b2ed41b8e'
const profile = {
  user_id: 7,
  username: 'ada',
  avatar: 'fox',
  scores: { 'forgot-password-x3': 3 },
  total_score: 3,
  completed_challenges: 1,
  attempt: {
    attempt_id: attemptId,
    challenge_slug: 'forgot-password-x3',
    score: 3,
    completed_at: '2026-10-29T01:23:45+00:00',
  },
}

test('claiming sends only the attempt id with session cookies and CSRF', async (t) => {
  const signal = new AbortController().signal
  const requests = []
  t.mock.method(globalThis, 'fetch', async (url, options) => {
    requests.push(url)
    assert.equal(options.credentials, 'same-origin')
    assert.equal(options.signal, signal)
    if (url === `${basePath}csrf/`)
      return Response.json({ csrfToken: 'fresh-token' })
    assert.equal(url, '/api/users/me/scores/forgot-password-x3/')
    assert.equal(options.method, 'POST')
    assert.equal(options.headers['X-CSRFToken'], 'fresh-token')
    assert.deepEqual(JSON.parse(options.body), { attempt_id: attemptId })
    return Response.json(profile)
  })
  assert.deepEqual(
    await resultClaimApi.claimAttempt(attemptId, 'forgot-password-x3', signal),
    profile,
  )
  assert.deepEqual(requests, [
    `${basePath}csrf/`,
    '/api/users/me/scores/forgot-password-x3/',
  ])
})

test('an expired login is reported as unauthorized', async (t) => {
  t.mock.method(globalThis, 'fetch', async (url) => {
    if (url === `${basePath}csrf/`) return Response.json({ csrfToken: 'token' })
    return Response.json(
      { detail: 'Authentication required.' },
      { status: 401 },
    )
  })
  await assert.rejects(
    resultClaimApi.claimAttempt(
      attemptId,
      'forgot-password-x3',
      new AbortController().signal,
    ),
    (error) =>
      error instanceof ResultClaimError &&
      error.reason === 'unauthorized' &&
      /Authentication required/.test(error.message),
  )
})

test('other claim failures are retryable failures', async (t) => {
  t.mock.method(globalThis, 'fetch', async (url) => {
    if (url === `${basePath}csrf/`) return Response.json({ csrfToken: 'token' })
    return new Response('Unavailable', { status: 503 })
  })
  await assert.rejects(
    resultClaimApi.claimAttempt(
      attemptId,
      'forgot-password-x3',
      new AbortController().signal,
    ),
    (error) =>
      error instanceof ResultClaimError &&
      error.reason === 'failed' &&
      /Could not notify|Could not connect|Could not save/.test(error.message),
  )
})
