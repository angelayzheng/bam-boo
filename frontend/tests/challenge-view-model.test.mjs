import assert from 'node:assert/strict'
import test from 'node:test'
import { ChallengeSession } from '../src/entities/challengeSession.ts'
import { toChallengeViewModel } from '../src/challenge/viewModels/challengeViewModel.ts'

const challenge = {
  name: 'Forgot Password x3',
  slug: 'forgot-password-x3',
  challenge_date: '2026-11-18',
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

const choice = (id, choiceId, text = id) => ({
  ...turn(id, 'response', text),
  choiceId,
})

const snapshot = (overrides = {}) => ({
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

const viewModelFor = (snapshotValue, mutate) => {
  const session = new ChallengeSession(snapshotValue)
  if (mutate) mutate(session)
  return toChallengeViewModel({
    status: snapshotValue.stage === 'completed' ? 'complete' : 'ready',
    session: session.snapshot(),
  })
}

test('loading and error outputs remain display-only defaults', () => {
  assert.equal(toChallengeViewModel(null).status, 'loading')
  const error = toChallengeViewModel({ status: 'error', message: 'Nope' })
  assert.equal(error.status, 'error')
  assert.equal(error.message, 'Nope')
  assert.equal(error.name, null)
})

test('a tone-stage snapshot exposes the opening and first step', () => {
  const viewModel = viewModelFor(snapshot())
  assert.equal(viewModel.name, challenge.name)
  assert.equal(viewModel.category, challenge.category)
  assert.equal(viewModel.stage, 'tone')
  assert.equal(viewModel.dateLabel, 'Wednesday, November 18, 2026')
  assert.deepEqual(viewModel.opening, {
    key: '/media/c1.txt',
    type: 'question',
    text: 'Customer opening',
    transcriptUrl: '/media/c1.txt',
    audioUrl: '/media/c1.mp3',
  })
  assert.deepEqual(viewModel.path, [])
  assert.equal(viewModel.stepNumber, 1)
  assert.equal(viewModel.progressPercent, 33)
})

test('a conversation snapshot maps server choices and selection state', () => {
  const viewModel = viewModelFor(
    snapshot({
      stage: 'conversation',
      conversation: [turn('c1', 'question', 'Customer opening')],
      choices: [choice('a1', '0', 'Agent reply'), choice('a2', '1', 'Other')],
      toneCorrect: true,
      toneTime: 4.6,
      toneSpeedCorrect: true,
    }),
    (session) => session.selectChoice('0'),
  )
  assert.equal(viewModel.stage, 'response')
  assert.equal(viewModel.stepNumber, 2)
  assert.equal(viewModel.progressPercent, 67)
  assert.equal(viewModel.toneTime, 5)
  assert.equal(viewModel.toneCorrect, true)
  assert.equal(viewModel.toneSpeedCorrect, true)
  assert.deepEqual(viewModel.options, [
    { key: '0', text: 'Agent reply', selected: true },
    { key: '1', text: 'Other', selected: false },
  ])
  assert.equal(viewModel.conversationFinished, false)
})

test('a terminal conversation exposes the continue state', () => {
  const viewModel = viewModelFor(
    snapshot({
      stage: 'conversation',
      conversation: [turn('c1', 'question')],
      choices: [],
    }),
  )
  assert.equal(viewModel.conversationFinished, true)
})

test('pending and error flags are presentation values, not domain objects', () => {
  const viewModel = viewModelFor(
    snapshot({
      stage: 'conversation',
      conversation: [turn('c1', 'question')],
      choices: [choice('a1', '0')],
    }),
    (session) => {
      session.beginChoiceSubmission()
      session.recordChoiceError('Could not send your response.')
    },
  )
  assert.equal(viewModel.choicePending, false)
  assert.equal(viewModel.choiceError, 'Could not send your response.')
  assert.equal('session' in viewModel, false)
  assert.equal('challenge' in viewModel, false)
  assert.equal('result' in viewModel, false)
})

test('an action snapshot exposes the completion step and draft', () => {
  const viewModel = viewModelFor(
    snapshot({ stage: 'action', conversation: [turn('c1', 'question')] }),
    (session) => session.changeAction('Reset the password.'),
  )
  assert.equal(viewModel.stage, 'action')
  assert.equal(viewModel.stepNumber, 3)
  assert.equal(viewModel.progressPercent, 100)
  assert.equal(viewModel.nextAction, 'Reset the password.')
})

test('a completed snapshot reports the complete status with action fields', () => {
  const viewModel = viewModelFor(
    snapshot({
      stage: 'completed',
      conversation: [turn('c1', 'question')],
      toneCorrect: false,
      toneTime: 12,
      toneSpeedCorrect: false,
      actionCorrect: true,
      score: 1,
      requiredAction: 'reset password',
      completedAt: '2026-11-11T12:00:00+00:00',
    }),
  )
  assert.equal(viewModel.status, 'complete')
  assert.equal(viewModel.stage, 'action')
  assert.equal(viewModel.conversationFinished, false)
})
