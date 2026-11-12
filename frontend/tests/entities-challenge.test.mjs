import assert from 'node:assert/strict'
import test from 'node:test'
import {
  ChallengeSession,
  normalizeToneInput,
} from '../src/entities/challengeSession.ts'

const turn = (key, type, children = []) => ({
  node_key: key,
  type,
  transcript_url: `/media/${key}.txt`,
  audio_url: `/media/${key}.mp3`,
  text: key,
  children,
})

const endings = ['c5', 'c6', 'c7'].map((key) => turn(key, 'question'))
const followups = endings.map((ending, index) =>
  turn(`a${index + 4}`, 'response', [ending]),
)
const customers = followups.map((followup, index) =>
  turn(`c${index + 2}`, 'question', [followup]),
)
const replies = customers.map((customer, index) =>
  turn(`a${index + 1}`, 'response', [customer]),
)
const root = turn('c1', 'question', replies)

const challenge = {
  name: 'Forgot Password x3',
  slug: 'forgot-password-x3',
  challenge_date: '2026-10-15',
  difficulty: 1,
  category: 'account',
  required_action: 'reset password',
  conversation_tree: root,
}

const session = () => new ChallengeSession(challenge, 1000)

test('tone input keeps at most two whitespace-separated words', () => {
  assert.equal(normalizeToneInput('very calm'), 'very calm')
  assert.equal(normalizeToneInput('very  calm'), 'very calm')
  assert.equal(
    normalizeToneInput('frustrated and tired today'),
    'frustrated and',
  )
  assert.equal(normalizeToneInput(''), '')
})

test('a session starts on the tone stage with the tree root', () => {
  const state = session().snapshot()
  assert.equal(state.stage, 'tone')
  assert.deepEqual(state.path, [root])
  assert.equal(state.tonePending, false)
  assert.equal(state.tone, '')
})

test('tone submission records the result and moves to the response stage', () => {
  const s = session()
  s.changeTone('very calm')
  s.beginToneSubmission()
  assert.equal(s.snapshot().tonePending, true)
  s.recordToneResult(true, 9)
  const state = s.snapshot()
  assert.equal(state.tonePending, false)
  assert.equal(state.toneCorrect, true)
  assert.equal(state.toneTime, 9)
  assert.equal(state.stage, 'response')
})

test('a tone failure stays on the tone stage and can be retried', () => {
  const s = session()
  s.beginToneSubmission()
  s.recordToneError('Tone scoring is unavailable. Please try again.')
  const state = s.snapshot()
  assert.equal(state.tonePending, false)
  assert.equal(state.stage, 'tone')
  assert.equal(
    state.toneError,
    'Tone scoring is unavailable. Please try again.',
  )
  s.beginToneSubmission()
  assert.equal(s.snapshot().tonePending, true)
})

test('sending a response grows the path and chains the next audio', () => {
  const s = session()
  s.selectResponse(replies[0])
  s.sendResponse()
  assert.deepEqual(
    s.snapshot().path.map(({ node_key }) => node_key),
    ['c1', 'a1', 'c2'],
  )
  assert.equal(s.snapshot().activeAudio, '/media/a1.txt')
  assert.equal(s.snapshot().selectedResponse, null)
})

test('sending without a selection does nothing', () => {
  const s = session()
  s.sendResponse()
  assert.deepEqual(s.snapshot().path, [root])
})

test('audio chaining advances to the next turn and clears at the end', () => {
  const s = session()
  s.selectResponse(replies[0])
  s.sendResponse()
  s.advanceAudio('/media/a1.txt')
  assert.equal(s.snapshot().activeAudio, '/media/c2.txt')
  s.advanceAudio('/media/c2.txt')
  assert.equal(s.snapshot().activeAudio, '')
  s.advanceAudio('/media/unknown.txt')
  assert.equal(s.snapshot().activeAudio, '')
})

test('continuing from a finished conversation opens the action stage', () => {
  const s = session()
  s.selectResponse(replies[0])
  s.sendResponse()
  assert.throws(() => s.continueToAction(), /Finish the conversation/)
  s.selectResponse(followups[0])
  s.sendResponse()
  s.continueToAction()
  assert.equal(s.snapshot().stage, 'action')
  assert.equal(s.snapshot().activeAudio, '')
})

test('a session rejects a conversation tree that does not start with a customer question', () => {
  assert.throws(
    () =>
      new ChallengeSession(
        { ...challenge, conversation_tree: turn('a1', 'response') },
        1000,
      ),
    /no conversation tree/,
  )
})

test('buildResult uses whole-word matching and injected identifiers', () => {
  const s = session()
  s.recordToneResult(false, 24)
  s.changeAction('I will reset the customer’s password.')
  const result = s.buildResult('attempt-1', '2026-11-11T12:00:00.000Z')
  assert.deepEqual(result, {
    challengeSlug: 'forgot-password-x3',
    attemptId: 'attempt-1',
    completedAt: '2026-11-11T12:00:00.000Z',
    toneCorrect: false,
    toneTime: 24,
    actionCorrect: true,
  })
})

test('buildResult rejects an action that does not match', () => {
  const s = session()
  s.changeAction('Freeze the card and open a fraud claim.')
  assert.equal(s.buildResult('attempt-1', 'now').actionCorrect, false)
})
