import assert from 'node:assert/strict'
import test from 'node:test'
import { ChallengeSession } from '../src/entities/challengeSession.ts'
import { toChallengeViewModel } from '../src/challenge/viewModels/challengeViewModel.ts'

const followup = {
  type: 'question',
  node_key: 'c2',
  transcript_url: '/media/c2.txt',
  audio_url: '/media/c2.mp3',
  text: 'Customer follow-up',
  children: [],
}
const reply = {
  type: 'response',
  node_key: 'a1',
  transcript_url: '/media/a1.txt',
  audio_url: '/media/a1.mp3',
  text: 'Agent reply',
  children: [followup],
}
const root = {
  type: 'question',
  node_key: 'c1',
  transcript_url: '/media/c1.txt',
  audio_url: '/media/c1.mp3',
  text: 'Customer opening',
  children: [reply],
}
const challenge = {
  name: 'Forgot Password x3',
  slug: 'forgot-password-x3',
  challenge_date: '2026-11-18',
  difficulty: 1,
  category: 'account',
  required_action: 'reset password',
  conversation_tree: root,
}

test('challenge view model exposes display-ready values, not domain objects', () => {
  const session = new ChallengeSession(challenge, 1000)
  session.changeTone('calm')
  session.beginToneSubmission()
  session.recordToneResult(true, 4)
  session.selectResponse(reply)

  const viewModel = toChallengeViewModel({
    status: 'ready',
    challenge,
    session: session.snapshot(),
  })

  assert.equal(viewModel.name, challenge.name)
  assert.equal(viewModel.category, challenge.category)
  assert.equal(viewModel.stage, 'response')
  assert.equal(viewModel.dateLabel, 'Wednesday, November 18, 2026')
  assert.deepEqual(viewModel.opening, {
    key: '/media/c1.txt',
    type: 'question',
    text: 'Customer opening',
    transcriptUrl: '/media/c1.txt',
    audioUrl: '/media/c1.mp3',
  })
  assert.deepEqual(viewModel.path, [
    {
      key: '/media/c1.txt',
      type: 'question',
      text: 'Customer opening',
      transcriptUrl: '/media/c1.txt',
      audioUrl: '/media/c1.mp3',
    },
  ])
  assert.deepEqual(viewModel.options, [
    { key: '/media/a1.txt', text: 'Agent reply', selected: true },
  ])
  assert.equal('session' in viewModel, false)
  assert.equal('challenge' in viewModel, false)
  assert.equal('result' in viewModel, false)
})
