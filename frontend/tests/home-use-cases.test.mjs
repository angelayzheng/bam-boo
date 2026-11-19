import assert from 'node:assert/strict'
import test from 'node:test'
import { LoadCalendarInteractor } from '../src/home/useCases/loadCalendar/loadCalendarInteractor.ts'
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

test('loadCalendar builds the month from progress and summaries', async () => {
  const { outputs, boundary } = recorder()
  const interactor = new LoadCalendarInteractor(
    {
      async loadProgress() {
        return {
          scores: { demo: 3 },
          loginDays: ['2026-11-17', '2026-11-18'],
        }
      },
    },
    boundary,
  )

  await interactor.execute({
    summaries: [
      summary('missing', '2026-11-16'),
      summary('demo', '2026-11-17'),
    ],
    referenceDate: '2026-11-18',
    username: 'kenny',
    signal: new AbortController().signal,
  })

  assert.equal(outputs.length, 1)
  const output = outputs[0]
  assert.equal(output.status, 'ready')
  assert.equal(
    output.calendar.days.find((day) => day.date === '2026-11-17')?.score,
    3,
  )
  assert.equal(
    output.calendar.days.find((day) => day.date === '2026-11-16')?.missed,
    true,
  )
  assert.equal(output.calendar.streak, 2)
})

test('loadCalendar reports progress failures with an empty calendar', async () => {
  const { outputs, boundary } = recorder()
  const interactor = new LoadCalendarInteractor(
    {
      async loadProgress() {
        throw new Error('progress unavailable')
      },
    },
    boundary,
  )

  await interactor.execute({
    summaries: [summary('demo', '2026-11-17')],
    referenceDate: '2026-11-18',
    username: 'kenny',
    signal: new AbortController().signal,
  })

  assert.equal(outputs.length, 1)
  assert.equal(outputs[0].status, 'error')
  assert.equal(outputs[0].message, 'progress unavailable')
  assert.ok(outputs[0].calendar.days.length > 0)
  assert.equal(
    outputs[0].calendar.days.find((day) => day.date === '2026-11-17')?.score,
    null,
  )
})

test('loadCalendar skips aborted requests', async () => {
  const { outputs, boundary } = recorder()
  const controller = new AbortController()
  controller.abort()
  const interactor = new LoadCalendarInteractor(
    {
      async loadProgress() {
        assert.fail('should not load progress for an aborted request')
      },
    },
    boundary,
  )

  await interactor.execute({
    summaries: [],
    referenceDate: '2026-11-18',
    username: 'kenny',
    signal: controller.signal,
  })

  assert.equal(outputs.length, 0)
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
