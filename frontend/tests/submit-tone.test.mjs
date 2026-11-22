import assert from 'node:assert/strict'
import test from 'node:test'
import { ChallengeSession } from '../src/entities/challengeSession.ts'
import { SubmitToneInteractor } from '../src/challenge/useCases/submitTone/submitToneInteractor.ts'
import { createSessionStore } from '../src/challenge/useCases/sessionStore.ts'

const challenge = {
  name: 'Forgot Password x3',
  slug: 'forgot-password-x3',
  challenge_date: '2026-10-15',
  difficulty: 1,
  category: 'account',
}

const opening = {
  id: 'c1',
  type: 'question',
  transcriptUrl: '/media/c1.txt',
  audioUrl: '/media/c1.mp3',
  text: 'Customer opening',
}

const snapshot = (overrides = {}) => ({
  attemptId: 'attempt-1',
  stage: 'tone',
  challenge,
  opening,
  conversation: [],
  choices: [],
  toneCorrect: null,
  toneTime: null,
  toneSpeedCorrect: null,
  toneSimilarity: null,
  actionCorrect: null,
  score: null,
  requiredAction: null,
  completedAt: null,
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

function make(gateway) {
  const output = new FakeOutputBoundary()
  const store = createSessionStore()
  store.set(new ChallengeSession(snapshot()))
  const interactor = new SubmitToneInteractor(store, gateway, output)
  return { output, store, interactor }
}

test('grades the tone through the attempt and applies the conversation snapshot', async () => {
  const { output, store, interactor } = make({
    submitTone: async (attemptId, answer, signal) => {
      assert.equal(attemptId, 'attempt-1')
      assert.equal(answer, 'concerned')
      assert.ok(signal instanceof AbortSignal)
      return snapshot({
        stage: 'conversation',
        conversation: [opening],
        toneCorrect: true,
        toneTime: 3.4,
        toneSpeedCorrect: true,
        toneSimilarity: 0.8,
      })
    },
  })
  await interactor.execute({
    answer: 'concerned',
    signal: new AbortController().signal,
  })
  assert.deepEqual(
    output.outputs.map(({ session }) => session.tonePending),
    [true, false],
  )
  const final = output.outputs.at(-1).session
  assert.equal(final.stage, 'conversation')
  assert.equal(final.toneCorrect, true)
  assert.equal(final.toneTime, 3.4)
  assert.equal(final.toneSpeedCorrect, true)
  assert.equal(store.get().snapshot().stage, 'conversation')
})

test('a scoring failure stays on the tone step with a retryable message', async () => {
  const { output, interactor } = make({
    submitTone: async () => {
      throw new Error('Tone scoring is unavailable. Please try again.')
    },
  })
  await interactor.execute({
    answer: 'calm',
    signal: new AbortController().signal,
  })
  const final = output.outputs.at(-1).session
  assert.equal(final.stage, 'tone')
  assert.equal(final.tonePending, false)
  assert.equal(
    final.toneError,
    'Tone scoring is unavailable. Please try again.',
  )
})

test('unknown errors fall back to the generic tone message', async () => {
  const { output, interactor } = make({
    submitTone: async () => {
      throw 'boom'
    },
  })
  await interactor.execute({
    answer: 'calm',
    signal: new AbortController().signal,
  })
  assert.equal(
    output.outputs.at(-1).session.toneError,
    'Tone scoring failed. Please try again.',
  )
})

test('a cancelled request presents nothing beyond the pending state', async () => {
  const controller = new AbortController()
  const { output, interactor } = make({
    submitTone: async () => {
      controller.abort()
      throw new Error('aborted')
    },
  })
  await interactor.execute({ answer: 'calm', signal: controller.signal })
  assert.equal(output.outputs.length, 1)
  assert.equal(output.outputs[0].session.tonePending, true)
})

test('setTone normalizes the answer through the entity', () => {
  const { output, interactor } = make({
    submitTone: async () => snapshot(),
  })
  interactor.setTone({ answer: 'frustrated and tired today' })
  assert.equal(output.outputs.at(-1).session.tone, 'frustrated and')
})

test('a pending submission cannot be started twice', async () => {
  let calls = 0
  let release
  const pending = new Promise((resolve) => {
    release = resolve
  })
  const { output, interactor } = make({
    submitTone: async () => {
      calls += 1
      await pending
      return snapshot({ stage: 'conversation', conversation: [opening] })
    },
  })
  const first = interactor.execute({
    answer: 'calm',
    signal: new AbortController().signal,
  })
  await interactor.execute({
    answer: 'calm',
    signal: new AbortController().signal,
  })
  release()
  await first
  assert.equal(calls, 1)
  assert.equal(output.outputs.length, 2)
})

test('a non-tone stage cannot submit another tone', async () => {
  let calls = 0
  const output = new FakeOutputBoundary()
  const store = createSessionStore()
  store.set(
    new ChallengeSession(
      snapshot({ stage: 'conversation', conversation: [opening] }),
    ),
  )
  const interactor = new SubmitToneInteractor(
    store,
    {
      submitTone: async () => {
        calls += 1
        return snapshot()
      },
    },
    output,
  )
  await interactor.execute({
    answer: 'calm',
    signal: new AbortController().signal,
  })
  assert.equal(calls, 0)
  assert.equal(output.outputs.length, 0)
})
