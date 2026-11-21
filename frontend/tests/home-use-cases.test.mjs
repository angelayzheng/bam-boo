import assert from 'node:assert/strict'
import test from 'node:test'
import { LoadLeaderboardInteractor } from '../src/home/useCases/loadLeaderboard/loadLeaderboardInteractor.ts'
import { LoadTodayChallengeInteractor } from '../src/home/useCases/loadTodayChallenge/loadTodayChallengeInteractor.ts'

const summary = (slug, challengeDate) => ({
  name: slug,
  slug,
  challenge_date: challengeDate,
  difficulty: 1,
  category: 'demo',
})

const recorder = () => {
  const outputs = []
  return {
    outputs,
    boundary: {
      present(output) {
        outputs.push(output)
      },
    },
  }
}

test('loadTodayChallenge presents the selected summary', () => {
  const { outputs, boundary } = recorder()
  const interactor = new LoadTodayChallengeInteractor(boundary)
  const first = summary('first', '2026-11-16')
  const demo = summary('forgot-password-x3', '2026-11-17')

  interactor.execute({ summaries: [first, demo] })

  assert.equal(outputs.length, 1)
  assert.equal(outputs[0].challenge, demo)
})

test('loadLeaderboard ranks entries and marks the current user', async () => {
  const { outputs, boundary } = recorder()
  const interactor = new LoadLeaderboardInteractor(
    {
      async loadLeaderboard() {
        return [
          { userId: 1, username: 'high', avatar: 'fox', totalScore: 9 },
          { userId: 2, username: 'you', avatar: 'owl', totalScore: 5 },
        ]
      },
    },
    boundary,
  )

  await interactor.execute({
    currentUserId: 2,
    signal: new AbortController().signal,
  })

  assert.equal(outputs.length, 1)
  assert.equal(outputs[0].status, 'ready')
  assert.equal(outputs[0].currentUserId, 2)
  assert.equal(outputs[0].entries.length, 2)
})

test('loadLeaderboard reports failures', async () => {
  const { outputs, boundary } = recorder()
  const interactor = new LoadLeaderboardInteractor(
    {
      async loadLeaderboard() {
        throw new Error('leaderboard unavailable')
      },
    },
    boundary,
  )

  await interactor.execute({
    currentUserId: null,
    signal: new AbortController().signal,
  })

  assert.equal(outputs.length, 1)
  assert.equal(outputs[0].status, 'error')
  assert.equal(outputs[0].message, 'leaderboard unavailable')
})
