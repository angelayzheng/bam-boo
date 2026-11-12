import assert from 'node:assert/strict'
import test from 'node:test'
import { ChallengeSession } from '../src/entities/challengeSession.ts'
import { AdvanceConversationInteractor } from '../src/useCases/advanceConversation/advanceConversationInteractor.ts'
import { createSessionStore } from '../src/useCases/sessionStore.ts'

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

function make() {
  const output = new FakeOutputBoundary()
  const store = createSessionStore()
  const session = new ChallengeSession(demo, 1000)
  store.set(session)
  const interactor = new AdvanceConversationInteractor(store, output)
  return { output, session, interactor }
}

test('selecting and sending a reply grows the path and chains audio', () => {
  const { output, interactor } = make()
  interactor.selectResponse({ response: replies[0] })
  assert.equal(output.outputs.at(-1).session.selectedResponse, replies[0])
  interactor.sendResponse()
  const session = output.outputs.at(-1).session
  assert.deepEqual(
    session.path.map(({ node_key }) => node_key),
    ['c1', 'a1', 'c2'],
  )
  assert.equal(session.activeAudio, '/media/a1.txt')
  assert.equal(session.selectedResponse, null)
})

test('a reply from another branch is rejected', () => {
  const { interactor } = make()
  const unavailable = turn('other', 'response')
  interactor.selectResponse({ response: unavailable })
  assert.throws(() => interactor.sendResponse(), /current conversation turn/)
})

test('a terminal reply finishes the conversation and can continue', () => {
  const { output, interactor } = make()
  interactor.selectResponse({ response: replies[0] })
  interactor.sendResponse()
  interactor.selectResponse({ response: followups[0] })
  interactor.sendResponse()
  interactor.continueToAction()
  const session = output.outputs.at(-1).session
  assert.equal(session.stage, 'action')
  assert.equal(session.activeAudio, '')
})

test('audio endings chain to the next turn and clear at the end', () => {
  const { output, interactor } = make()
  interactor.selectResponse({ response: replies[0] })
  interactor.sendResponse()
  interactor.audioEnded({ transcriptUrl: '/media/a1.txt' })
  assert.equal(output.outputs.at(-1).session.activeAudio, '/media/c2.txt')
  interactor.audioEnded({ transcriptUrl: '/media/c2.txt' })
  assert.equal(output.outputs.at(-1).session.activeAudio, '')
})

test('sending without a selection presents the unchanged session', () => {
  const { output, interactor } = make()
  interactor.sendResponse()
  assert.deepEqual(
    output.outputs.at(-1).session.path.map(({ node_key }) => node_key),
    ['c1'],
  )
})
