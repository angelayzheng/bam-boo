import assert from 'node:assert/strict'
import test from 'node:test'
import {
  ChallengeSession,
  normalizeToneInput,
} from '../src/entities/challengeSession.ts'

const challenge = {
  name: 'Forgot Password x3',
  slug: 'forgot-password-x3',
  challenge_date: '2026-10-15',
  difficulty: 1,
  category: 'account',
}

const turn = (id, type, text = id) => ({
  id,
  type,
  transcriptUrl: `/media/${id}.txt`,
  audioUrl: `/media/${id}.mp3`,
  text,
})

const baseSnapshot = (overrides = {}) => ({
  attemptId: 'attempt-1',
  stage: 'tone',
  challenge,
  opening: turn('c1', 'question', 'Customer opening'),
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

const session = (overrides) => new ChallengeSession(baseSnapshot(overrides))

test('tone input keeps at most two whitespace-separated words', () => {
  assert.equal(normalizeToneInput('very calm'), 'very calm')
  assert.equal(normalizeToneInput('very  calm'), 'very calm')
  assert.equal(
    normalizeToneInput('frustrated and tired today'),
    'frustrated and',
  )
  assert.equal(normalizeToneInput(''), '')
})

test('a session starts from the server snapshot on the tone stage', () => {
  const state = session().snapshot()
  assert.equal(state.stage, 'tone')
  assert.equal(state.attemptId, 'attempt-1')
  assert.deepEqual(state.conversation, [])
  assert.equal(state.tonePending, false)
  assert.equal(state.tone, '')
})

test('tone success applies the returned snapshot and clears pending state', () => {
  const current = session()
  const choice = { ...turn('a1', 'response'), choiceId: '0' }
  current.changeTone('very calm')
  current.beginToneSubmission()
  assert.equal(current.snapshot().tonePending, true)
  current.recordToneSuccess(
    baseSnapshot({
      stage: 'conversation',
      conversation: [turn('c1', 'question', 'Customer opening')],
      choices: [choice],
      toneCorrect: true,
      toneTime: 4.2,
      toneSpeedCorrect: true,
      toneSimilarity: 0.8,
    }),
  )
  const state = current.snapshot()
  assert.equal(state.tonePending, false)
  assert.equal(state.stage, 'conversation')
  assert.equal(state.toneCorrect, true)
  assert.equal(state.toneTime, 4.2)
  assert.deepEqual(state.choices, [choice])
})

test('a tone failure stays on the tone stage and can be retried', () => {
  const current = session()
  current.beginToneSubmission()
  current.recordToneError('Tone scoring is unavailable. Please try again.')
  const state = current.snapshot()
  assert.equal(state.tonePending, false)
  assert.equal(state.stage, 'tone')
  assert.equal(
    state.toneError,
    'Tone scoring is unavailable. Please try again.',
  )
  current.beginToneSubmission()
  assert.equal(current.snapshot().tonePending, true)
})

test('selecting a choice is validated against the current options', () => {
  const choice = { ...turn('a1', 'response'), choiceId: '0' }
  const current = session({
    stage: 'conversation',
    conversation: [turn('c1', 'question')],
    choices: [choice],
  })
  assert.throws(() => current.selectChoice('9'), /current conversation turn/)
  current.selectChoice('0')
  assert.equal(current.snapshot().selectedChoiceId, '0')
})

test('a choice response appends the branch and chains the response audio', () => {
  const choice = { ...turn('a1', 'response'), choiceId: '0' }
  const current = session({
    stage: 'conversation',
    conversation: [turn('c1', 'question')],
    choices: [choice],
  })
  current.selectChoice('0')
  current.beginChoiceSubmission()
  current.recordChoiceSuccess(
    baseSnapshot({
      stage: 'conversation',
      conversation: [
        turn('c1', 'question'),
        turn('a1', 'response'),
        turn('c2', 'question'),
      ],
      choices: [],
    }),
  )
  const state = current.snapshot()
  assert.equal(state.choicePending, false)
  assert.deepEqual(
    state.conversation.map(({ id }) => id),
    ['c1', 'a1', 'c2'],
  )
  assert.equal(state.activeAudio, '/media/a1.txt')
  assert.equal(state.selectedChoiceId, null)
})

test('a choice failure stays on the conversation stage with an error', () => {
  const current = session({
    stage: 'conversation',
    conversation: [turn('c1', 'question')],
    choices: [{ ...turn('a1', 'response'), choiceId: '0' }],
  })
  current.beginChoiceSubmission()
  current.recordChoiceError('Could not send your response.')
  const state = current.snapshot()
  assert.equal(state.choicePending, false)
  assert.equal(state.choiceError, 'Could not send your response.')
})

test('audio progress advances through the conversation and clears at the end', () => {
  const current = session({
    stage: 'conversation',
    conversation: [turn('c1', 'question'), turn('a1', 'response')],
  })
  current.advanceAudio('/media/c1.txt')
  assert.equal(current.snapshot().activeAudio, '/media/a1.txt')
  current.advanceAudio('/media/a1.txt')
  assert.equal(current.snapshot().activeAudio, '')
  current.advanceAudio('/media/unknown.txt')
  assert.equal(current.snapshot().activeAudio, '')
})

test('continuing applies the action-stage snapshot and clears audio', () => {
  const current = session({
    stage: 'conversation',
    conversation: [turn('c1', 'question')],
  })
  current.beginContinue()
  current.recordContinueSuccess(
    baseSnapshot({
      stage: 'action',
      conversation: [turn('c1', 'question')],
    }),
  )
  assert.equal(current.snapshot().stage, 'action')
  assert.equal(current.snapshot().continuePending, false)
  assert.equal(current.snapshot().activeAudio, '')
})

test('a completed snapshot builds the result the results page uses', () => {
  const current = session()
  current.changeAction('I will reset the customer’s password.')
  current.beginActionSubmission()
  current.recordActionResult(
    baseSnapshot({
      stage: 'completed',
      conversation: [turn('c1', 'question'), turn('a1', 'response')],
      toneCorrect: true,
      toneTime: 5.4,
      toneSpeedCorrect: true,
      toneSimilarity: 0.9,
      actionCorrect: true,
      score: 3,
      requiredAction: 'reset password',
      completedAt: '2026-11-11T12:00:00+00:00',
    }),
  )
  assert.deepEqual(current.buildResult(), {
    attemptId: 'attempt-1',
    challenge,
    completedAt: '2026-11-11T12:00:00+00:00',
    toneCorrect: true,
    toneTime: 5.4,
    toneSpeedCorrect: true,
    toneSimilarity: 0.9,
    actionCorrect: true,
    score: 3,
    requiredAction: 'reset password',
  })
})

test('an incomplete session cannot build a result', () => {
  assert.throws(() => session().buildResult(), /not complete/)
})
