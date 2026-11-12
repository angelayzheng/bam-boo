import assert from 'node:assert/strict'
import test from 'node:test'
import { ChallengeSession } from '../src/entities/challengeSession.ts'
import { CompleteChallengeInteractor } from '../src/useCases/completeChallenge/completeChallengeInteractor.ts'
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

test('setAction records the next action through the entity', () => {
  const output = new FakeOutputBoundary()
  const session = new ChallengeSession(demo, 1000)
  const store = createSessionStore()
  store.set(session)
  const interactor = new CompleteChallengeInteractor(
    store,
    output,
    { randomId: () => 'attempt-uuid' },
    { now: () => 1700000000000 },
  )
  interactor.setAction({ action: 'Escalate to the team lead.' })
  assert.equal(
    output.outputs.at(-1).session.nextAction,
    'Escalate to the team lead.',
  )
})

test('completion builds a result with injected identifiers and timing', () => {
  const output = new FakeOutputBoundary()
  const session = new ChallengeSession(demo, 1000)
  session.changeTone('frustrated')
  session.recordToneResult(true, 6)
  session.continueToAction()
  session.changeAction('I will reset the customer’s password.')
  const store = createSessionStore()
  store.set(session)
  const interactor = new CompleteChallengeInteractor(
    store,
    output,
    { randomId: () => 'attempt-uuid' },
    { now: () => 1700000000000 },
  )
  interactor.execute()
  const completed = output.outputs[0]
  assert.equal(completed.status, 'complete')
  assert.deepEqual(completed.result, {
    challengeSlug: 'forgot-password-x3',
    attemptId: 'attempt-uuid',
    completedAt: new Date(1700000000000).toISOString(),
    toneCorrect: true,
    toneTime: 6,
    actionCorrect: true,
  })
  assert.equal(completed.session.stage, 'action')
})

test('a mismatched action still completes with a false answer flag', () => {
  const output = new FakeOutputBoundary()
  const session = new ChallengeSession(demo, 1000)
  session.changeAction('Freeze the card and open a fraud claim.')
  const store = createSessionStore()
  store.set(session)
  const interactor = new CompleteChallengeInteractor(
    store,
    output,
    { randomId: () => 'attempt-uuid' },
    { now: () => 1700000000000 },
  )
  interactor.execute()
  assert.equal(output.outputs[0].result.actionCorrect, false)
})
