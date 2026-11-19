import assert from 'node:assert/strict'
import test from 'node:test'
import { selectHomeChallenge } from '../src/entities/dailyChallenge.ts'
import {
  buildTrainingCalendar,
  computeStreak,
} from '../src/entities/trainingCalendar.ts'

const summary = (slug, challengeDate) => ({
  name: slug,
  slug,
  challenge_date: challengeDate,
  difficulty: 1,
  category: 'demo',
})

test('builds a Sunday-first month grid with scores, misses, and today', () => {
  const referenceDate = '2026-11-18'
  const calendar = buildTrainingCalendar({
    summaries: [
      summary('a', '2026-11-16'),
      summary('b', '2026-11-17'),
      summary('c', '2026-11-18'),
    ],
    scores: { b: 3 },
    loginDays: ['2026-11-16', '2026-11-17', '2026-11-18'],
    referenceDate,
    progressKnown: true,
  })

  const firstOfMonth = new Date(2026, 10, 1)
  assert.equal(calendar.year, 2026)
  assert.equal(calendar.monthIndex, 10)
  assert.equal(
    calendar.days.length,
    Math.ceil((firstOfMonth.getDay() + 30) / 7) * 7,
  )
  assert.equal(
    calendar.days.findIndex((day) => day.day === 1),
    firstOfMonth.getDay(),
  )

  const scored = calendar.days.find((day) => day.date === '2026-11-17')
  assert.equal(scored?.hasChallenge, true)
  assert.equal(scored?.score, 3)
  assert.equal(scored?.missed, false)

  const missed = calendar.days.find((day) => day.date === '2026-11-16')
  assert.equal(missed?.hasChallenge, true)
  assert.equal(missed?.score, null)
  assert.equal(missed?.missed, true)

  const today = calendar.days.find((day) => day.date === referenceDate)
  assert.equal(today?.isToday, true)
  assert.equal(today?.missed, false)
  assert.equal(calendar.streak, 3)
})

test('does not mark missed days for guests or unavailable progress', () => {
  const calendar = buildTrainingCalendar({
    summaries: [summary('a', '2026-11-16')],
    scores: {},
    loginDays: [],
    referenceDate: '2026-11-18',
    progressKnown: false,
  })

  const missed = calendar.days.find((day) => day.date === '2026-11-16')
  assert.equal(missed?.hasChallenge, true)
  assert.equal(missed?.missed, false)
  assert.equal(calendar.streak, 0)
})

test('streak continues from yesterday when today is missing', () => {
  assert.equal(computeStreak(['2026-11-16', '2026-11-17'], '2026-11-18'), 2)
  assert.equal(computeStreak(['2026-11-16', '2026-11-17'], '2026-11-19'), 0)
  assert.equal(computeStreak([], '2026-11-18'), 0)
})

test('selectHomeChallenge prefers the demo and falls back to the first', () => {
  const first = summary('first', '2026-11-16')
  const demo = summary('forgot-password-x3', '2026-11-17')
  assert.equal(selectHomeChallenge([first, demo]), demo)
  assert.equal(selectHomeChallenge([first]), first)
  assert.equal(selectHomeChallenge([]), null)
})
