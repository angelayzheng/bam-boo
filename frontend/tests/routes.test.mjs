import assert from 'node:assert/strict'
import test from 'node:test'
import {
  challengePath,
  getRoute,
  parseChallengePath,
  resultsPath,
} from '../src/routes.ts'

test('account pages resolve before any challenge has loaded', () => {
  assert.equal(getRoute('/login'), 'login')
  assert.equal(getRoute('/signup'), 'signup')
  assert.equal(getRoute('/profile'), 'profile')
  assert.equal(getRoute('/'), 'home')
  assert.equal(getRoute('/challenges/'), 'home')
})

test('challenge and results routes are identified by their slug', () => {
  assert.equal(getRoute(challengePath('charged-twice')), 'challenge')
  assert.equal(getRoute(resultsPath('charged-twice')), 'results')
  assert.equal(getRoute('/challenges/forgot-password-x3'), 'challenge')
  assert.equal(getRoute('/challenges/foo/bar'), 'home')
  assert.equal(getRoute('/unknown'), 'home')
})

test('parseChallengePath extracts the slug and completion flag', () => {
  assert.deepEqual(parseChallengePath('/challenges/charged-twice'), {
    slug: 'charged-twice',
    results: false,
  })
  assert.deepEqual(parseChallengePath('/challenges/charged-twice/complete'), {
    slug: 'charged-twice',
    results: true,
  })
  assert.equal(parseChallengePath('/challenges/'), null)
})
