import assert from 'node:assert/strict'
import test from 'node:test'
import { leaderboardApi } from '../src/home/dataAccessInterface/leaderboardGatewayApi.ts'
import { profileApi } from '../src/home/dataAccessInterface/profileGatewayApi.ts'

test('profile loads the signed-in scores and login days', async (t) => {
  const controller = new AbortController()
  t.mock.method(globalThis, 'fetch', async (url, { signal }) => {
    assert.equal(url, '/api/users/kenny/')
    assert.equal(signal, controller.signal)
    return Response.json({
      challenge_scores: { demo: 3 },
      login_days: ['2026-11-17', '2026-11-18'],
    })
  })

  const progress = await profileApi.loadProgress('kenny', controller.signal)
  assert.deepEqual(progress.scores, { demo: 3 })
  assert.deepEqual(progress.loginDays, ['2026-11-17', '2026-11-18'])
})

test('profile rejects malformed progress payloads', async (t) => {
  for (const payload of [
    {},
    { challenge_scores: null, login_days: [] },
    { challenge_scores: { demo: '3' }, login_days: [] },
    { challenge_scores: {}, login_days: '2026-11-18' },
  ]) {
    t.mock.method(globalThis, 'fetch', async () => Response.json(payload))
    await assert.rejects(
      profileApi.loadProgress('kenny', new AbortController().signal),
      /unexpected format/,
    )
  }
})

test('leaderboard loads ranked entries', async (t) => {
  t.mock.method(globalThis, 'fetch', async (url) => {
    assert.equal(url, '/api/users/leaderboard/')
    return Response.json({
      leaderboard: [
        {
          user_id: 2,
          username: 'kenny',
          avatar: 'fox',
          total_score: 9,
        },
      ],
    })
  })

  const entries = await leaderboardApi.loadLeaderboard(
    new AbortController().signal,
  )
  assert.deepEqual(entries, [
    { userId: 2, username: 'kenny', avatar: 'fox', totalScore: 9 },
  ])
})

test('leaderboard rejects malformed entries', async (t) => {
  for (const payload of [
    {},
    { leaderboard: 'nope' },
    { leaderboard: [{ user_id: 2, username: 'kenny' }] },
  ]) {
    t.mock.method(globalThis, 'fetch', async () => Response.json(payload))
    await assert.rejects(
      leaderboardApi.loadLeaderboard(new AbortController().signal),
      /unexpected format/,
    )
  }
})
