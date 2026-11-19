import assert from 'node:assert/strict'
import test from 'node:test'
import { profileGateway } from '../src/profile/dataAccessInterface/profileGatewayApi.ts'

test('profile loads and normalizes the signed-in account progress', async (t) => {
  const signal = new AbortController().signal
  t.mock.method(globalThis, 'fetch', async (url, options) => {
    assert.equal(url, '/api/users/7/profile/')
    assert.equal(options.signal, signal)
    assert.equal(options.cache, 'no-store')
    return Response.json({
      user_id: 7,
      username: 'ada',
      avatar: 'fox',
      total_score: 2,
      completed_challenges: 1,
      scores: { 'forgot-password-x3': 2 },
    })
  })

  assert.deepEqual(await profileGateway.loadProfile(7, signal), {
    userId: 7,
    username: 'ada',
    avatar: 'fox',
    totalScore: 2,
    completedChallenges: 1,
    scores: { 'forgot-password-x3': 2 },
  })
})

test('profile rejects malformed payloads', async (t) => {
  for (const payload of [
    {},
    { user_id: 7, username: 'ada', avatar: 'fox', total_score: 2 },
    {
      user_id: 7,
      username: 'ada',
      avatar: 'fox',
      total_score: 2,
      completed_challenges: 1,
      scores: { demo: '3' },
    },
  ]) {
    t.mock.method(globalThis, 'fetch', async () => Response.json(payload))
    await assert.rejects(
      profileGateway.loadProfile(7, new AbortController().signal),
      /unexpected format/,
    )
  }
})

test('profile reports backend failures', async (t) => {
  t.mock.method(
    globalThis,
    'fetch',
    async () => new Response('', { status: 503 }),
  )
  await assert.rejects(
    profileGateway.loadProfile(7, new AbortController().signal),
    /Could not load your profile/,
  )
})
