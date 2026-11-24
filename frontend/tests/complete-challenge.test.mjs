import assert from 'node:assert/strict'
import test from 'node:test'
import { ChallengeSession } from '../src/entities/challengeSession.ts'
import { CompleteChallengeInteractor } from '../src/challenge/useCases/completeChallenge/completeChallengeInteractor.ts'
import { createSessionStore } from '../src/challenge/useCases/sessionStore.ts'

const challenge = {
  name: 'Forgot Password x3',
  slug: 'forgot-password-x3',
  challenge_date: '2026-10-15',
  difficulty: 1,
  category: 'account',
}

const turn = (id, type, text = id) => ({
  id,
  type,
  transcriptUrl: `/media/${id}.txt`,
  audioUrl: `/media/${id}.mp3`,
  text,
})

const snapshot = (overrides = {}) => ({
  attemptId: 'attempt-1',
  stage: 'action',
  challenge,
  opening: turn('c1', 'question'),
  conversation: [turn('c1', 'question'), turn('a1', 'response')],
  choices: [],
  toneCorrect: true,
  toneTime: 6,
  toneSpeedCorrect: true,
  toneSimilarity: 0.8,
  actionCorrect: null,
  score: null,
  requiredAction: null,
  completedAt: null,
  ...overrides,
})

const completedSnapshot = (overrides = {}) =>
  snapshot({
    stage: 'completed',
    actionCorrect: true,
    score: 3,
    requiredAction: 'reset password',
    completedAt: '2026-11-11T12:00:00+00:00',
    ...overrides,
  })

class FakeOutputBoundary {
  constructor() {
    this.outputs = []
  }
  present(output) {
    this.outputs.push(output)
  }
}

function memoryStorage() {
  const cleared = []
  return {
    cleared,
    load: () => null,
    save: () => {},
    clear: (slug) => cleared.push(slug),
  }
}

function make(gateway, initial = snapshot()) {
  const output = new FakeOutputBoundary()
  const store = createSessionStore()
  store.set(new ChallengeSession(initial))
  const storage = memoryStorage()
  const interactor = new CompleteChallengeInteractor(
    store,
    gateway,
    output,
    storage,
  )
  return { output, store, storage, interactor }
}

test('setAction records the next action through the entity', () => {
  const { output, interactor } = make({
    submitAction: async () => completedSnapshot(),
  })
  interactor.setAction({ action: 'Escalate to the team lead.' })
  assert.equal(
    output.outputs.at(-1).session.nextAction,
    'Escalate to the team lead.',
  )
})

test('completion uses the server-graded snapshot and clears the attempt', async () => {
  const { output, storage, interactor } = make({
    submitAction: async (attemptId, answer, signal) => {
      assert.equal(attemptId, 'attempt-1')
      assert.equal(answer, 'I will reset the customer’s password.')
      assert.ok(signal instanceof AbortSignal)
      return completedSnapshot()
    },
  })
  interactor.setAction({ action: 'I will reset the customer’s password.' })
  await interactor.execute({ signal: new AbortController().signal })
  const completed = output.outputs.at(-1)
  assert.equal(completed.status, 'complete')
  assert.deepEqual(completed.result, {
    attemptId: 'attempt-1',
    challenge,
    completedAt: '2026-11-11T12:00:00+00:00',
    toneCorrect: true,
    toneTime: 6,
    toneSpeedCorrect: true,
    toneSimilarity: 0.8,
    actionCorrect: true,
    score: 3,
    requiredAction: 'reset password',
    userId: null,
    saved: false,
  })
  assert.deepEqual(storage.cleared, ['forgot-password-x3'])
})

test('completion preserves authenticated persistence state from the server', async () => {
  const { output, interactor } = make({
    submitAction: async () => completedSnapshot({ userId: 7, saved: true }),
  })
  interactor.setAction({ action: 'Reset the password.' })
  await interactor.execute({ signal: new AbortController().signal })

  assert.equal(output.outputs.at(-1).result.userId, 7)
  assert.equal(output.outputs.at(-1).result.saved, true)
})

test('a mismatched action still completes with the server score', async () => {
  const { output, interactor } = make({
    submitAction: async () =>
      completedSnapshot({ actionCorrect: false, score: 2 }),
  })
  interactor.setAction({ action: 'Freeze the card and open a fraud claim.' })
  await interactor.execute({ signal: new AbortController().signal })
  assert.equal(output.outputs.at(-1).result.actionCorrect, false)
  assert.equal(output.outputs.at(-1).result.score, 2)
})

test('a submit failure stays on the action stage with a retryable error', async () => {
  const { output, interactor } = make({
    submitAction: async () => {
      throw new Error('Could not submit your action. Please try again.')
    },
  })
  interactor.setAction({ action: 'Reset the password.' })
  await interactor.execute({ signal: new AbortController().signal })
  const state = output.outputs.at(-1).session
  assert.equal(output.outputs.at(-1).status, 'ready')
  assert.equal(state.stage, 'action')
  assert.equal(state.actionPending, false)
  assert.equal(
    state.actionError,
    'Could not submit your action. Please try again.',
  )
})

test('an empty action is not submitted', async () => {
  let calls = 0
  const { output, interactor } = make({
    submitAction: async () => {
      calls += 1
      return completedSnapshot()
    },
  })
  interactor.setAction({ action: '   ' })
  await interactor.execute({ signal: new AbortController().signal })
  assert.equal(calls, 0)
  assert.equal(output.outputs.at(-1).session.actionPending, false)
})

test('a non-action stage cannot complete', async () => {
  let calls = 0
  const { output, interactor } = make(
    {
      submitAction: async () => {
        calls += 1
        return completedSnapshot()
      },
    },
    snapshot({ stage: 'conversation' }),
  )
  interactor.setAction({ action: 'Reset the password.' })
  await interactor.execute({ signal: new AbortController().signal })
  assert.equal(calls, 0)
  assert.equal(output.outputs.length, 1)
})

test('an aborted request presents only the pending state', async () => {
  const controller = new AbortController()
  const { output, interactor } = make({
    submitAction: async () => {
      controller.abort()
      throw new Error('aborted')
    },
  })
  interactor.setAction({ action: 'Reset the password.' })
  await interactor.execute({ signal: controller.signal })
  assert.equal(output.outputs.length, 2)
  assert.equal(output.outputs.at(-1).session.actionPending, true)
  assert.equal(output.outputs.at(-1).session.actionError, '')
})
