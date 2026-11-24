import assert from 'node:assert/strict'
import test from 'node:test'
import { ChallengeSession } from '../src/entities/challengeSession.ts'
import { AdvanceConversationInteractor } from '../src/challenge/useCases/advanceConversation/advanceConversationInteractor.ts'
import { createSessionStore } from '../src/challenge/useCases/sessionStore.ts'

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

const choice = (id, choiceId) => ({ ...turn(id, 'response'), choiceId })

const snapshot = (overrides = {}) => ({
  attemptId: 'attempt-1',
  stage: 'conversation',
  challenge,
  opening: turn('c1', 'question'),
  conversation: [turn('c1', 'question')],
  choices: [choice('a1', '0')],
  toneCorrect: true,
  toneTime: 4,
  toneSpeedCorrect: true,
  toneSimilarity: 0.8,
  actionCorrect: null,
  score: null,
  requiredAction: null,
  completedAt: null,
  ...overrides,
})

class FakeOutputBoundary {
  constructor() {
    this.outputs = []
  }
  present(output) {
    this.outputs.push(output)
  }
}

function make(gateway, initial = snapshot()) {
  const output = new FakeOutputBoundary()
  const store = createSessionStore()
  store.set(new ChallengeSession(initial))
  const interactor = new AdvanceConversationInteractor(store, gateway, output)
  return { output, store, interactor }
}

test('selecting and sending a choice updates the conversation and chains audio', async () => {
  const { output, interactor } = make({
    chooseResponse: async (attemptId, choiceId, signal) => {
      assert.equal(attemptId, 'attempt-1')
      assert.equal(choiceId, '0')
      assert.ok(signal instanceof AbortSignal)
      return snapshot({
        conversation: [
          turn('c1', 'question'),
          turn('a1', 'response'),
          turn('c2', 'question'),
        ],
        choices: [choice('a4', '0')],
      })
    },
  })
  interactor.selectChoice({ choiceId: '0' })
  assert.equal(output.outputs.at(-1).session.selectedChoiceId, '0')
  await interactor.sendChoice({ signal: new AbortController().signal })
  const state = output.outputs.at(-1).session
  assert.deepEqual(
    state.conversation.map(({ id }) => id),
    ['c1', 'a1', 'c2'],
  )
  assert.equal(state.activeAudio, '/media/a1.txt')
  assert.equal(state.selectedChoiceId, null)
  assert.equal(state.choicePending, false)
})

test('an unavailable choice is rejected before any request', () => {
  const { interactor } = make({
    chooseResponse: async () => snapshot(),
  })
  assert.throws(
    () => interactor.selectChoice({ choiceId: '9' }),
    /current conversation turn/,
  )
})

test('a choice failure stays on the conversation stage with an error', async () => {
  const { output, interactor } = make({
    chooseResponse: async () => {
      throw new Error('The selected choice is unavailable.')
    },
  })
  interactor.selectChoice({ choiceId: '0' })
  await interactor.sendChoice({ signal: new AbortController().signal })
  const state = output.outputs.at(-1).session
  assert.equal(state.stage, 'conversation')
  assert.equal(state.choicePending, false)
  assert.equal(state.choiceError, 'The selected choice is unavailable.')
})

test('sending without a selection presents nothing', async () => {
  const { output, interactor } = make({
    chooseResponse: async () => snapshot(),
  })
  await interactor.sendChoice({ signal: new AbortController().signal })
  assert.equal(output.outputs.length, 0)
})

test('continue is rejected while responses are still available', async () => {
  let calls = 0
  const { output, interactor } = make({
    continueConversation: async () => {
      calls += 1
      return snapshot({ stage: 'action' })
    },
  })
  await interactor.continueToAction({
    signal: new AbortController().signal,
  })
  assert.equal(calls, 0)
  assert.equal(output.outputs.length, 0)
})

test('continuing from a finished conversation opens the action stage', async () => {
  const { output, interactor } = make(
    {
      continueConversation: async (attemptId, signal) => {
        assert.equal(attemptId, 'attempt-1')
        assert.ok(signal instanceof AbortSignal)
        return snapshot({ stage: 'action', choices: [] })
      },
    },
    snapshot({ choices: [], conversation: [turn('c1', 'question')] }),
  )
  await interactor.continueToAction({
    signal: new AbortController().signal,
  })
  const state = output.outputs.at(-1).session
  assert.equal(state.stage, 'action')
  assert.equal(state.continuePending, false)
  assert.equal(state.activeAudio, '')
})

test('a continue failure stays on the conversation stage with an error', async () => {
  const { output, interactor } = make(
    {
      continueConversation: async () => {
        throw new Error('Could not continue the challenge.')
      },
    },
    snapshot({ choices: [], conversation: [turn('c1', 'question')] }),
  )
  await interactor.continueToAction({
    signal: new AbortController().signal,
  })
  const state = output.outputs.at(-1).session
  assert.equal(state.stage, 'conversation')
  assert.equal(state.continuePending, false)
  assert.equal(state.continueError, 'Could not continue the challenge.')
})

test('audio endings chain to the next turn and clear at the end', () => {
  const { output, interactor } = make(
    {
      chooseResponse: async () => snapshot(),
    },
    snapshot({
      conversation: [
        turn('c1', 'question'),
        turn('a1', 'response'),
        turn('c2', 'question'),
      ],
      choices: [],
    }),
  )
  interactor.audioEnded({ transcriptUrl: '/media/c1.txt' })
  assert.equal(output.outputs.at(-1).session.activeAudio, '/media/a1.txt')
  interactor.audioEnded({ transcriptUrl: '/media/a1.txt' })
  assert.equal(output.outputs.at(-1).session.activeAudio, '/media/c2.txt')
  interactor.audioEnded({ transcriptUrl: '/media/c2.txt' })
  assert.equal(output.outputs.at(-1).session.activeAudio, '')
})
