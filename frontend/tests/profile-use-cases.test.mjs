import assert from 'node:assert/strict'
import test from 'node:test'
import { LoadUserProfileInteractor } from '../src/profile/useCases/loadUserProfile/loadUserProfileInteractor.ts'

const summary = (slug, name, challengeDate) => ({
  name,
  slug,
  challenge_date: challengeDate,
  difficulty: 1,
  category: 'demo',
})

const profile = {
  userId: 7,
  username: 'ada',
  avatar: 'fox',
  totalScore: 3,
  completedChallenges: 1,
  scores: { demo: 3 },
}

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

test('loadUserProfile presents the profile and joined progress', async () => {
  const { outputs, boundary } = recorder()
  const interactor = new LoadUserProfileInteractor(
    {
      async loadProfile() {
        return profile
      },
    },
    boundary,
  )

  await interactor.execute({
    userId: 7,
    summaries: [summary('demo', 'Demo challenge', '2026-11-17')],
    signal: new AbortController().signal,
  })

  assert.equal(outputs.length, 1)
  assert.equal(outputs[0].status, 'ready')
  assert.equal(outputs[0].profile, profile)
  assert.equal(outputs[0].progress.scores[0].name, 'Demo challenge')
  assert.equal(outputs[0].progress.scores[0].score, 3)
})

test('loadUserProfile reports failures', async () => {
  const { outputs, boundary } = recorder()
  const interactor = new LoadUserProfileInteractor(
    {
      async loadProfile() {
        throw new Error('profile unavailable')
      },
    },
    boundary,
  )

  await interactor.execute({
    userId: 7,
    summaries: [],
    signal: new AbortController().signal,
  })

  assert.equal(outputs.length, 1)
  assert.equal(outputs[0].status, 'error')
  assert.equal(outputs[0].message, 'profile unavailable')
})

test('loadUserProfile skips aborted requests', async () => {
  const { outputs, boundary } = recorder()
  const controller = new AbortController()
  controller.abort()
  const interactor = new LoadUserProfileInteractor(
    {
      async loadProfile() {
        assert.fail('should not load an aborted profile')
      },
    },
    boundary,
  )

  await interactor.execute({
    userId: 7,
    summaries: [],
    signal: controller.signal,
  })

  assert.equal(outputs.length, 0)
})
