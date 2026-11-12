import assert from 'node:assert/strict'
import test from 'node:test'
import { ChallengeSession } from '../src/entities/challengeSession.ts'
import { SubmitToneInteractor } from '../src/useCases/submitTone/submitToneInteractor.ts'
import { createSessionStore } from '../src/useCases/sessionStore.ts'

const root = {
  type: 'question',
  node_key: 'c1',
  transcript_url: 'media/c1.txt',
  audio_url: 'media/c1.mp3',
  text: 'Customer opening',
  children: [],
}
const demo = {
  name: 'Forgot Password x3',
  slug: 'forgot-password-x3',
  challenge_date: '2026-10-15',
  difficulty: 1,
  category: 'account',
  required_action: 'reset password',
  conversation_tree: root,
}

class FakeOutputBoundary {
  constructor() {
    this.outputs = []
  }
  present(output) {
    this.outputs.push(output)
  }
}

function make({ gateway, clock }) {
  const output = new FakeOutputBoundary()
  const store = createSessionStore()
  const session = new ChallengeSession(demo, 1000)
  store.set(session)
  const interactor = new SubmitToneInteractor(store, gateway, output, clock)
  return { output, session, interactor }
}

test('scores the tone, records elapsed time, and advances the stage', async () => {
  const { output, session, interactor } = make({
    gateway: {
      score: async (answer, slug, signal) => {
        assert.equal(answer, 'concerned')
        assert.equal(slug, 'forgot-password-x3')
        assert.ok(signal instanceof AbortSignal)
        return true
      },
    },
    clock: { now: () => 4000 },
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
  assert.equal(final.stage, 'response')
  assert.equal(final.toneCorrect, true)
  assert.equal(final.toneTime, 3)
  assert.equal(session.snapshot().stage, 'response')
})

test('a slow answer still records at least one second', async () => {
  const { output, interactor } = make({
    gateway: { score: async () => false },
    clock: { now: () => 1001 },
  })
  await interactor.execute({
    answer: 'calm',
    signal: new AbortController().signal,
  })
  assert.equal(output.outputs.at(-1).session.toneTime, 1)
  assert.equal(output.outputs.at(-1).session.toneCorrect, false)
})

test('a scoring failure stays on the tone step with a retryable message', async () => {
  const { output, interactor } = make({
    gateway: {
      score: async () => {
        throw new Error('Tone scoring is unavailable. Please try again.')
      },
    },
    clock: { now: () => 5000 },
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
    gateway: {
      score: async () => {
        throw 'boom'
      },
    },
    clock: { now: () => 5000 },
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
    gateway: {
      score: async () => {
        controller.abort()
        throw new Error('aborted')
      },
    },
    clock: { now: () => 5000 },
  })
  await interactor.execute({ answer: 'calm', signal: controller.signal })
  assert.equal(output.outputs.length, 1)
  assert.equal(output.outputs[0].session.tonePending, true)
})

test('setTone normalizes the answer through the entity', () => {
  const { output, interactor } = make({
    gateway: { score: async () => true },
    clock: { now: () => 5000 },
  })
  interactor.setTone({ answer: 'frustrated and tired today' })
  assert.equal(output.outputs.at(-1).session.tone, 'frustrated and')
})

test('a pending submission cannot be started twice', async () => {
  let calls = 0
  const { output, interactor } = make({
    gateway: {
      score: async () => {
        calls += 1
        return true
      },
    },
    clock: { now: () => 5000 },
  })
  const first = interactor.execute({
    answer: 'calm',
    signal: new AbortController().signal,
  })
  await interactor.execute({
    answer: 'calm',
    signal: new AbortController().signal,
  })
  await first
  assert.equal(calls, 1)
  assert.equal(output.outputs.length, 2)
})
