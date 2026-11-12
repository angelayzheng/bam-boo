import assert from 'node:assert/strict'
import test from 'node:test'
import { StartChallengeInteractor } from '../src/useCases/startChallenge/startChallengeInteractor.ts'
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

function make(gateway, clock = { now: () => 1000 }) {
  const output = new FakeOutputBoundary()
  const store = createSessionStore()
  const interactor = new StartChallengeInteractor(gateway, output, clock, store)
  return { output, store, interactor }
}

test('loads the challenge for the date and starts a session at the current time', async () => {
  const { output, store, interactor } = make({
    loadByDate: async () => demo,
  })
  await interactor.execute({
    date: '2026-10-15',
    signal: new AbortController().signal,
  })
  assert.deepEqual(
    output.outputs.map(({ status }) => status),
    ['loading', 'ready'],
  )
  const ready = output.outputs.at(-1)
  assert.equal(ready.challenge.slug, 'forgot-password-x3')
  assert.equal(ready.session.stage, 'tone')
  assert.equal(store.get().startedAt, 1000)
})

test('an empty database gives an actionable error', async () => {
  const { output, interactor } = make({
    loadByDate: async () => {
      throw new Error(
        'No recordings are available. Run the demo seed command in the setup guide.',
      )
    },
  })
  await interactor.execute({
    date: '2026-10-15',
    signal: new AbortController().signal,
  })
  assert.deepEqual(
    output.outputs.map(({ status }) => status),
    ['loading', 'error'],
  )
  assert.match(output.outputs.at(-1).message, /No recordings are available/)
})

test('a backend failure surfaces as an error output', async () => {
  const { output, interactor } = make({
    loadByDate: async () => {
      throw new Error('Could not load the recording.')
    },
  })
  await interactor.execute({
    date: '2026-10-15',
    signal: new AbortController().signal,
  })
  assert.equal(output.outputs.at(-1).status, 'error')
  assert.match(output.outputs.at(-1).message, /Could not load the recording/)
})

test('a cancelled request does not present beyond loading', async () => {
  const controller = new AbortController()
  const { output, interactor } = make({
    loadByDate: async () => {
      controller.abort()
      throw new Error('aborted')
    },
  })
  await interactor.execute({ date: '2026-10-15', signal: controller.signal })
  assert.deepEqual(
    output.outputs.map(({ status }) => status),
    ['loading'],
  )
})
