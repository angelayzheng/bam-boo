import assert from 'node:assert/strict'
import test from 'node:test'
import { resultStorage } from '../src/results/dataAccessInterface/resultStorageService.ts'

const result = {
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
}

function mockSessionStorage(t, { fail = false } = {}) {
  const values = new Map()
  const originalWindow = globalThis.window
  globalThis.window = {
    sessionStorage: {
      getItem: (key) => {
        if (fail) throw new Error('unavailable')
        return values.get(key) ?? null
      },
      setItem: (key, value) => {
        if (fail) throw new Error('unavailable')
        values.set(key, value)
      },
      removeItem: (key) => {
        if (fail) throw new Error('unavailable')
        values.delete(key)
      },
    },
  }
  t.after(() => {
    globalThis.window = originalWindow
  })
  return values
}

test('stores and clears the retained result', (t) => {
  mockSessionStorage(t)
  assert.equal(resultStorage.load(), null)
  resultStorage.save(result)
  assert.deepEqual(resultStorage.load(), result)
  resultStorage.clear()
  assert.equal(resultStorage.load(), null)
})

test('malformed retained results are removed', (t) => {
  const values = mockSessionStorage(t)
  values.set('bam-boo:last-challenge-result', '{not json')
  assert.equal(resultStorage.load(), null)
  assert.equal(values.size, 0)
})

test('unavailable session storage degrades safely', (t) => {
  mockSessionStorage(t, { fail: true })
  assert.equal(resultStorage.load(), null)
  assert.doesNotThrow(() => resultStorage.save(result))
  assert.doesNotThrow(() => resultStorage.clear())
})
