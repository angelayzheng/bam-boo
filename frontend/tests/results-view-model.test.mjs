import assert from 'node:assert/strict'
import test from 'node:test'
import {
  initialResultClaimViewModel,
  initialResultsViewModel,
  toResultClaimViewModel,
  toResultsViewModel,
  unavailableResultsViewModel,
} from '../src/results/viewModels/resultsViewModel.ts'

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
  toneTime: 8.4,
  toneSpeedCorrect: true,
  toneSimilarity: 0.8,
  actionCorrect: true,
  score: 3,
  requiredAction: 'reset password',
  userId: 7,
  saved: true,
  ...overrides,
})

test('loading and unavailable view models carry display messages', () => {
  assert.deepEqual(initialResultsViewModel(), {
    status: 'loading',
    message: 'Loading your result…',
  })
  assert.deepEqual(unavailableResultsViewModel('Gone'), {
    status: 'unavailable',
    message: 'Gone',
  })
})

test('a completed result maps to stars, heading, date, and achievements', () => {
  const viewModel = toResultsViewModel(result())
  assert.equal(viewModel.status, 'ready')
  assert.equal(viewModel.challengeName, 'Forgot Password x3')
  assert.equal(viewModel.dateLabel, 'Thursday, October 15, 2026')
  assert.equal(viewModel.heading, 'Beautifully handled.')
  assert.equal(viewModel.starCount, 3)
  assert.deepEqual(viewModel.stars, [true, true, true])
  assert.deepEqual(viewModel.achievements, [
    {
      earned: true,
      title: 'Read the tone',
      detail: 'You recognized the customer’s emotional tone.',
    },
    {
      earned: true,
      title: 'Quick instinct',
      detail: 'Tone identified in 8 seconds.',
    },
    {
      earned: true,
      title: 'Correct next step',
      detail: 'You identified the next step: reset password.',
    },
  ])
})

test('partial results expose missed achievements and the lower heading', () => {
  const viewModel = toResultsViewModel(
    result({
      toneCorrect: false,
      toneTime: 14.6,
      toneSpeedCorrect: false,
      actionCorrect: false,
      score: 0,
    }),
  )
  assert.equal(viewModel.status, 'ready')
  assert.equal(viewModel.heading, 'Good work. Keep listening.')
  assert.equal(viewModel.starCount, 0)
  assert.deepEqual(viewModel.stars, [false, false, false])
  assert.deepEqual(viewModel.achievements, [
    {
      earned: false,
      title: 'Read the tone',
      detail: 'Your answer did not match the customer’s emotional tone.',
    },
    {
      earned: false,
      title: 'Quick instinct',
      detail: 'Tone identified in 15 seconds. Aim for 10.',
    },
    {
      earned: false,
      title: 'Correct next step',
      detail: 'Expected next step: reset password.',
    },
  ])
})

test('claim view models expose the correct actions for each state', () => {
  assert.deepEqual(initialResultClaimViewModel(), {
    status: 'checking',
    message: 'Checking your account before saving…',
    showLogin: false,
    showProfile: false,
    canRetry: false,
  })
  assert.deepEqual(toResultClaimViewModel({ status: 'guest' }), {
    status: 'guest',
    message: 'Your result is kept in this browser session.',
    showLogin: true,
    showProfile: false,
    canRetry: false,
  })
  assert.deepEqual(toResultClaimViewModel({ status: 'saving' }), {
    status: 'saving',
    message: 'Saving your score…',
    showLogin: false,
    showProfile: false,
    canRetry: false,
  })
  assert.deepEqual(
    toResultClaimViewModel({
      status: 'saved',
      result: result(),
      claimed: true,
    }),
    {
      status: 'saved',
      message: 'Score saved to your profile. Your best score counts.',
      showLogin: false,
      showProfile: true,
      canRetry: false,
    },
  )
  assert.deepEqual(
    toResultClaimViewModel({
      status: 'error',
      message: 'Could not save your score.',
    }),
    {
      status: 'error',
      message: 'Could not save your score.',
      showLogin: false,
      showProfile: false,
      canRetry: true,
    },
  )
  assert.equal(
    toResultClaimViewModel({ status: 'other-account' }).message,
    'This result belongs to another session. Retry the challenge to save a score to this account.',
  )
  assert.equal(
    toResultClaimViewModel({ status: 'invalid' }).message,
    'This result has no completion details. Retry the challenge to record a new completion.',
  )
  assert.deepEqual(toResultClaimViewModel({ status: 'unauthorized' }), {
    status: 'unauthorized',
    message: 'Your session expired. Log in to save your score.',
    showLogin: true,
    showProfile: false,
    canRetry: false,
  })
})
