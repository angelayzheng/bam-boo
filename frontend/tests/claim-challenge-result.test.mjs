import assert from 'node:assert/strict'
import test from 'node:test'
import { ClaimChallengeResultInteractor } from '../src/results/useCases/claimChallengeResult/claimChallengeResultInteractor.ts'
import { ResultClaimError } from '../src/results/boundaries/dataAccessInterfaces.ts'

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
  userId: null,
  saved: false,
  ...overrides,
})

const user = { id: 7, username: 'ada', email: 'ada@example.com' }

class FakeOutputBoundary {
  constructor() {
    this.outputs = []
  }
  present(output) {
    this.outputs.push(output)
  }
}

function memoryStorage() {
  const saves = []
  return {
    saves,
    load: () => null,
    save: (next) => saves.push(next),
    clear: () => {},
  }
}

function make(gateway) {
  const output = new FakeOutputBoundary()
  const storage = memoryStorage()
  return {
    output,
    storage,
    interactor: new ClaimChallengeResultInteractor(gateway, storage, output),
  }
}

const input = ({
  result: value = result(),
  currentUser = user,
  signal,
  sessionLoading = false,
} = {}) => ({
  result: value,
  user: currentUser,
  sessionLoading,
  signal: signal ?? new AbortController().signal,
})

test('session loading is checked before any claim decision', async () => {
  let calls = 0
  const { output, interactor } = make({
    claimAttempt: async () => {
      calls += 1
    },
  })
  await interactor.execute(input({ sessionLoading: true }))
  assert.equal(calls, 0)
  assert.equal(output.outputs[0].status, 'checking')
})

test('guests are not claimed', async () => {
  let calls = 0
  const { output, interactor } = make({
    claimAttempt: async () => {
      calls += 1
    },
  })
  await interactor.execute(input({ currentUser: null }))
  assert.equal(calls, 0)
  assert.equal(output.outputs[0].status, 'guest')
})

test('already saved results are presented without another claim', async () => {
  let calls = 0
  const { output, interactor } = make({
    claimAttempt: async () => {
      calls += 1
    },
  })
  await interactor.execute(
    input({ result: result({ userId: 7, saved: true }) }),
  )
  assert.equal(calls, 0)
  assert.deepEqual(output.outputs[0], {
    status: 'saved',
    result: result({ userId: 7, saved: true }),
    claimed: false,
  })
})

test('results owned by another account are not claimed', async () => {
  let calls = 0
  const { output, interactor } = make({
    claimAttempt: async () => {
      calls += 1
    },
  })
  await interactor.execute(input({ result: result({ userId: 9 }) }))
  assert.equal(calls, 0)
  assert.equal(output.outputs[0].status, 'other-account')
})

test('invalid results are rejected before any claim', async () => {
  let calls = 0
  const { output, interactor } = make({
    claimAttempt: async () => {
      calls += 1
    },
  })
  await interactor.execute(input({ result: result({ score: 9 }) }))
  assert.equal(calls, 0)
  assert.equal(output.outputs[0].status, 'invalid')
})

test('a claimable result is claimed, persisted, and marked saved', async () => {
  const { output, storage, interactor } = make({
    claimAttempt: async (attemptId, slug, signal) => {
      assert.equal(attemptId, 'attempt-1')
      assert.equal(slug, 'forgot-password-x3')
      assert.ok(signal instanceof AbortSignal)
      return { total_score: 3 }
    },
  })
  await interactor.execute(input())
  assert.deepEqual(
    output.outputs.map(({ status }) => status),
    ['saving', 'saved'],
  )
  assert.deepEqual(output.outputs.at(-1), {
    status: 'saved',
    result: result({ userId: 7, saved: true }),
    claimed: true,
  })
  assert.deepEqual(storage.saves, [result({ userId: 7, saved: true })])
})

test('an expired session presents unauthorized instead of a generic error', async () => {
  const { output, interactor } = make({
    claimAttempt: async () => {
      throw new ResultClaimError('Authentication required.', 'unauthorized')
    },
  })
  await interactor.execute(input())
  assert.deepEqual(
    output.outputs.map(({ status }) => status),
    ['saving', 'unauthorized'],
  )
})

test('a failed claim presents a retryable error', async () => {
  const { output, interactor } = make({
    claimAttempt: async () => {
      throw new ResultClaimError(
        'Could not save your score. Please try again.',
        'failed',
      )
    },
  })
  await interactor.execute(input())
  assert.equal(output.outputs.at(-1).status, 'error')
  assert.equal(
    output.outputs.at(-1).message,
    'Could not save your score. Please try again.',
  )
})

test('a cancelled claim presents nothing beyond saving', async () => {
  const controller = new AbortController()
  const { output, interactor } = make({
    claimAttempt: async () => {
      controller.abort()
      throw new Error('aborted')
    },
  })
  await interactor.execute(input({ signal: controller.signal }))
  assert.deepEqual(
    output.outputs.map(({ status }) => status),
    ['saving'],
  )
})
