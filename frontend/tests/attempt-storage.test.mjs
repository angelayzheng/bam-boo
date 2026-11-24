import assert from 'node:assert/strict'
import test from 'node:test'
import { attemptStorage } from '../src/challenge/dataAccessInterface/attemptStorage.ts'

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

test('stores one attempt id per challenge slug', (t) => {
  const values = mockSessionStorage(t)
  attemptStorage.save('forgot-password-x3', 'attempt-1')
  attemptStorage.save('charged-twice', 'attempt-2')
  assert.equal(attemptStorage.load('forgot-password-x3'), 'attempt-1')
  assert.equal(attemptStorage.load('charged-twice'), 'attempt-2')
  assert.equal(values.size, 2)
})

test('clearing one challenge leaves other attempts intact', (t) => {
  mockSessionStorage(t)
  attemptStorage.save('forgot-password-x3', 'attempt-1')
  attemptStorage.save('charged-twice', 'attempt-2')
  attemptStorage.clear('forgot-password-x3')
  assert.equal(attemptStorage.load('forgot-password-x3'), null)
  assert.equal(attemptStorage.load('charged-twice'), 'attempt-2')
})

test('unavailable session storage degrades to an empty default', (t) => {
  mockSessionStorage(t, { fail: true })
  assert.equal(attemptStorage.load('forgot-password-x3'), null)
  assert.doesNotThrow(() =>
    attemptStorage.save('forgot-password-x3', 'attempt-1'),
  )
  assert.doesNotThrow(() => attemptStorage.clear('forgot-password-x3'))
})
