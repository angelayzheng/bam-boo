import assert from 'node:assert/strict'
import test from 'node:test'
import { StartChallengeInteractor } from '../src/challenge/useCases/startChallenge/startChallengeInteractor.ts'
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

function memoryStorage(initial = {}) {
  const values = new Map(Object.entries(initial))
  return {
    values,
    load: (slug) => values.get(slug) ?? null,
    save: (slug, attemptId) => values.set(slug, attemptId),
    clear: (slug) => values.delete(slug),
  }
}

function make({ gateway, storage = memoryStorage() }) {
  const output = new FakeOutputBoundary()
  const store = createSessionStore()
  const interactor = new StartChallengeInteractor(
    gateway,
    storage,
    output,
    store,
  )
  return { output, store, storage, interactor }
}

const input = (signal = new AbortController().signal) => ({
  slug: 'forgot-password-x3',
  signal,
})

test('starting a new challenge stores the attempt and presents the opening', async () => {
  const { output, store, storage, interactor } = make({
    gateway: {
      start: async (slug, signal) => {
        assert.equal(slug, 'forgot-password-x3')
        assert.ok(signal instanceof AbortSignal)
        return snapshot()
      },
      load: async () => {
        throw new Error('should not resume without a stored attempt')
      },
    },
  })
  await interactor.execute(input())
  assert.deepEqual(
    output.outputs.map(({ status }) => status),
    ['loading', 'ready'],
  )
  const ready = output.outputs.at(-1)
  assert.equal(ready.session.stage, 'tone')
  assert.equal(ready.session.attemptId, 'attempt-1')
  assert.equal(store.get().snapshot().attemptId, 'attempt-1')
  assert.equal(storage.load('forgot-password-x3'), 'attempt-1')
})

test('an in-progress stored attempt resumes instead of starting a new run', async () => {
  const storage = memoryStorage({ 'forgot-password-x3': 'stored-attempt' })
  let startCalls = 0
  const {
    output,
    storage: usedStorage,
    interactor,
  } = make({
    storage,
    gateway: {
      load: async (attemptId) => {
        assert.equal(attemptId, 'stored-attempt')
        return snapshot({
          attemptId: 'stored-attempt',
          stage: 'conversation',
          conversation: [opening],
        })
      },
      start: async () => {
        startCalls += 1
        return snapshot()
      },
    },
  })
  await interactor.execute(input())
  assert.equal(startCalls, 0)
  assert.equal(output.outputs.at(-1).session.stage, 'conversation')
  assert.equal(usedStorage.load('forgot-password-x3'), 'stored-attempt')
})

test('a completed stored attempt is discarded and a new run starts', async () => {
  const storage = memoryStorage({ 'forgot-password-x3': 'completed-attempt' })
  let cleared = null
  const originalClear = storage.clear
  storage.clear = (slug) => {
    cleared = slug
    originalClear(slug)
  }
  const { output, interactor } = make({
    storage,
    gateway: {
      load: async () =>
        snapshot({
          attemptId: 'completed-attempt',
          stage: 'completed',
          score: 2,
        }),
      start: async () => snapshot({ attemptId: 'new-attempt' }),
    },
  })
  await interactor.execute(input())
  assert.equal(cleared, 'forgot-password-x3')
  assert.equal(output.outputs.at(-1).session.attemptId, 'new-attempt')
})

test('a stale stored attempt starts a new run when loading returns null', async () => {
  const storage = memoryStorage({ 'forgot-password-x3': 'stale-attempt' })
  const { output, interactor } = make({
    storage,
    gateway: {
      load: async () => null,
      start: async () => snapshot({ attemptId: 'new-attempt' }),
    },
  })
  await interactor.execute(input())
  assert.equal(output.outputs.at(-1).session.attemptId, 'new-attempt')
})

test('a backend failure surfaces as an error output', async () => {
  const { output, interactor } = make({
    gateway: {
      start: async () => {
        throw new Error('Could not start the challenge.')
      },
    },
  })
  await interactor.execute(input())
  assert.deepEqual(
    output.outputs.map(({ status }) => status),
    ['loading', 'error'],
  )
  assert.match(output.outputs.at(-1).message, /Could not start the challenge/)
})

test('an aborted request does not present beyond loading', async () => {
  const controller = new AbortController()
  const { output, interactor } = make({
    gateway: {
      start: async () => {
        controller.abort()
        throw new Error('aborted')
      },
    },
  })
  await interactor.execute(input(controller.signal))
  assert.deepEqual(
    output.outputs.map(({ status }) => status),
    ['loading'],
  )
})
