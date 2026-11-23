import assert from 'node:assert/strict'
import test from 'node:test'
import { RestoreChallengeResultInteractor } from '../src/results/useCases/restoreChallengeResult/restoreChallengeResultInteractor.ts'

const result = (overrides = {}) => ({
  attemptId: 'attempt-1',
  challenge: {
    name: 'Forgot Password x3',
    slug: 'forgot-password-x3',
    challenge_date: '2026-10-15',
    difficulty: 1,
    category: 'account',
  },
  completedAt: '2026-10-29T01:23:45+00:00',
  toneCorrect: true,
  toneTime: 8,
  toneSpeedCorrect: true,
  toneSimilarity: 0.8,
  actionCorrect: true,
  score: 3,
  requiredAction: 'reset password',
  userId: 7,
  saved: true,
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

function memoryStorage(initial = null) {
  let value = initial
  const saves = []
  let clears = 0
  return {
    saves,
    get clears() {
      return clears
    },
    load: () => value,
    save: (next) => {
      value = next
      saves.push(next)
    },
    clear: () => {
      value = null
      clears += 1
    },
  }
}

function make(storage) {
  const output = new FakeOutputBoundary()
  return {
    output,
    interactor: new RestoreChallengeResultInteractor(storage, output),
  }
}

test('a fresh completion seed is validated, persisted, and presented', () => {
  const storage = memoryStorage()
  const { output, interactor } = make(storage)
  interactor.execute({ slug: 'forgot-password-x3', seed: result() })
  assert.equal(output.outputs.length, 1)
  assert.equal(output.outputs[0].status, 'ready')
  assert.deepEqual(output.outputs[0].result, result())
  assert.deepEqual(storage.saves, [result()])
})

test('a reload restores the retained result from storage', () => {
  const { output, interactor } = make(memoryStorage(result()))
  interactor.execute({ slug: 'forgot-password-x3', seed: null })
  assert.equal(output.outputs[0].status, 'ready')
  assert.deepEqual(output.outputs[0].result, result())
})

test('an invalid seed falls back to a valid stored result', () => {
  const { output, interactor } = make(memoryStorage(result()))
  interactor.execute({
    slug: 'forgot-password-x3',
    seed: { ...result(), score: 9 },
  })
  assert.equal(output.outputs[0].status, 'ready')
  assert.deepEqual(output.outputs[0].result, result())
})

test('a result for another challenge route is unavailable without clearing it', () => {
  const storage = memoryStorage(result())
  const { output, interactor } = make(storage)
  interactor.execute({ slug: 'charged-twice', seed: null })
  assert.equal(output.outputs[0].status, 'unavailable')
  assert.equal(storage.clears, 0)
  assert.deepEqual(storage.load(), result())
})

test('a null slug restores any retained result for background claiming', () => {
  const { output, interactor } = make(memoryStorage(result()))
  interactor.execute({ slug: null, seed: null })
  assert.equal(output.outputs[0].status, 'ready')
})

test('malformed stored results are cleared and presented as unavailable', () => {
  const storage = memoryStorage({ attemptId: 'broken' })
  const { output, interactor } = make(storage)
  interactor.execute({ slug: 'forgot-password-x3', seed: null })
  assert.equal(output.outputs[0].status, 'unavailable')
  assert.match(output.outputs[0].message, /no longer available/)
  assert.equal(storage.clears, 1)
})

test('a missing stored result is unavailable', () => {
  const { output, interactor } = make(memoryStorage())
  interactor.execute({ slug: 'forgot-password-x3', seed: null })
  assert.equal(output.outputs[0].status, 'unavailable')
})
