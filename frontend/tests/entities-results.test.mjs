import assert from 'node:assert/strict'
import test from 'node:test'
import {
  claimEligibility,
  markResultClaimed,
  parseChallengeResult,
  resultOutcomes,
} from '../src/entities/challengeResultSummary.ts'

const challenge = {
  name: 'Forgot Password x3',
  slug: 'forgot-password-x3',
  challenge_date: '2026-10-15',
  difficulty: 1,
  category: 'account',
}

const result = (overrides = {}) => ({
  attemptId: '627e5d91-c343-44ae-b6ab-532b2ed41b8e',
  challenge,
  completedAt: '2026-10-29T01:23:45+00:00',
  toneCorrect: true,
  toneTime: 8,
  toneSpeedCorrect: true,
  toneSimilarity: 0.8,
  actionCorrect: true,
  score: 3,
  requiredAction: 'reset password',
  userId: 7,
  saved: false,
  ...overrides,
})

const user = { id: 7, username: 'ada', email: 'ada@example.com' }

test('parses and normalizes a complete stored result', () => {
  assert.deepEqual(parseChallengeResult(result()), result())
  assert.deepEqual(
    parseChallengeResult(
      result({ toneSimilarity: 2, userId: 'seven', saved: 'yes' }),
    ),
    result({ toneSimilarity: null, userId: null, saved: false }),
  )
})

test('rejects malformed stored results', () => {
  for (const value of [
    null,
    {},
    result({ attemptId: '' }),
    result({ completedAt: '' }),
    result({ toneCorrect: 'yes' }),
    result({ toneTime: -1 }),
    result({ toneSpeedCorrect: null }),
    result({ actionCorrect: 'true' }),
    result({ score: 4 }),
    result({ score: 1.5 }),
    result({ requiredAction: '' }),
    result({ challenge: { slug: 'missing-fields' } }),
  ]) {
    assert.equal(parseChallengeResult(value), null)
  }
})

test('claim eligibility distinguishes loading, guests, saved, and ownership', () => {
  assert.equal(claimEligibility(result(), user, true), 'checking')
  assert.equal(claimEligibility(result(), null, false), 'guest')
  assert.equal(
    claimEligibility(result({ userId: 9 }), user, false),
    'other-account',
  )
  assert.equal(
    claimEligibility(result({ userId: 9, saved: true }), user, false),
    'other-account',
  )
  assert.equal(claimEligibility(result({ saved: true }), user, false), 'saved')
  assert.equal(claimEligibility(result(), user, false), 'claimable')
  assert.equal(
    claimEligibility({ ...result(), score: 9 }, user, false),
    'invalid',
  )
})

test('claiming marks the result with its account and saved state', () => {
  assert.deepEqual(markResultClaimed(result(), 7), result({ saved: true }))
})

test('result outcomes expose server-graded achievements and stars', () => {
  assert.deepEqual(resultOutcomes(result()), {
    tone: true,
    speed: true,
    action: true,
    stars: 3,
  })
})
