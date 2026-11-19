import assert from 'node:assert/strict'
import test from 'node:test'
import { buildUserProfileProgress } from '../src/entities/userProfileProgress.ts'

const summary = (slug, name, challengeDate) => ({
  name,
  slug,
  challenge_date: challengeDate,
  difficulty: 1,
  category: 'demo',
})

test('joins best scores with challenge metadata', () => {
  const progress = buildUserProfileProgress(
    {
      totalScore: 5,
      completedChallenges: 2,
      scores: { demo: 3, unknown: 2 },
    },
    [summary('demo', 'Demo challenge', '2026-11-17')],
  )

  assert.equal(progress.totalScore, 5)
  assert.equal(progress.completedChallenges, 2)
  assert.deepEqual(progress.scores, [
    {
      slug: 'demo',
      name: 'Demo challenge',
      challengeDate: '2026-11-17',
      score: 3,
    },
    {
      slug: 'unknown',
      name: 'Challenge unknown',
      challengeDate: null,
      score: 2,
    },
  ])
})

test('keeps an empty score list', () => {
  const progress = buildUserProfileProgress(
    { totalScore: 0, completedChallenges: 0, scores: {} },
    [],
  )
  assert.deepEqual(progress.scores, [])
})
