import assert from 'node:assert/strict'
import test from 'node:test'
import * as routes from '../src/routes.ts'

test('the assigned level opens the level screen', () => {
  assert.match(routes.levelPath, /^\/levels\/\d{4}-\d{2}-\d{2}$/)
  assert.equal(routes.getRoute(routes.levelPath), 'level')
})

test('the completion URL opens the results screen', () => {
  assert.equal(routes.resultsPath, `${routes.levelPath}/complete`)
  assert.equal(routes.getRoute(routes.resultsPath), 'results')
})

test('home and unknown URLs return to the home screen', () => {
  for (const path of [
    '/',
    '/unknown',
    '/levels/unassigned',
    `${routes.levelPath}/other`,
  ]) {
    assert.equal(routes.getRoute(path), 'home')
  }
})
