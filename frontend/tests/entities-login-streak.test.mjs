import assert from 'node:assert/strict'
import test from 'node:test'
import { selectHomeChallenge } from '../src/entities/dailyChallenge.ts'
import { computeStreak } from '../src/entities/loginStreak.ts'

const summary = (slug, challengeDate) => ({
  name: slug,
  slug,
  challenge_date: challengeDate,
  difficulty: 1,
  category: 'demo',
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
