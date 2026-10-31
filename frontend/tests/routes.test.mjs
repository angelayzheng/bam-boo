import assert from 'node:assert/strict'
import test from 'node:test'
import { challengePath, getRoute, resultsPath } from '../src/routes.ts'

test('account pages resolve before any challenge has loaded', () => {
  assert.equal(getRoute('/login'), 'login')
  assert.equal(getRoute('/signup'), 'signup')
  assert.equal(getRoute('/profile'), 'profile')
  assert.equal(getRoute('/'), 'home')
  assert.equal(getRoute('/challenges/undefined'), 'home')
})

test('challenge and results routes still use the loaded challenge date', () => {
  const date = '2026-10-15'
  assert.equal(getRoute(challengePath(date), date), 'challenge')
  assert.equal(getRoute(resultsPath(date), date), 'results')
  assert.equal(getRoute('/challenges/2026-10-16', date), 'home')
  assert.equal(getRoute('/unknown', date), 'home')
})
