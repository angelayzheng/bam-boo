import assert from 'node:assert/strict'
import test from 'node:test'
import { matchesAnswer, respond, responseOptions } from '../src/conversation.ts'

const turn = (key, type, children = []) => ({
  node_key: key,
  type,
  text_file: `${key}.txt`,
  audio_file: `${key}.mp3`,
  transcript_url: `/media/${key}.txt`,
  audio_url: `/media/${key}.mp3`,
  text: key,
  children,
})

test('each reply follows its own customer branch and exposes the next agent turn', () => {
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

  replies.forEach((reply, index) => {
    const start = [root]
    const firstExchange = respond(start, reply)
    assert.deepEqual(
      firstExchange.map(({ node_key }) => node_key),
      ['c1', `a${index + 1}`, `c${index + 2}`],
    )
    assert.deepEqual(responseOptions(firstExchange), [followups[index]])
    const finished = respond(firstExchange, followups[index])
    assert.equal(finished.at(-1), endings[index])
    assert.deepEqual(responseOptions(finished), [])
    assert.deepEqual(start, [root], 'starting history is preserved for retry')
  })
})

test('a reply from another branch cannot be selected', () => {
  const unavailable = turn('other', 'response')
  const root = turn('c1', 'question', [turn('a1', 'response')])
  assert.throws(() => respond([root], unavailable), /current conversation turn/)
})

test('a terminal agent response also finishes the conversation', () => {
  const agent = turn('a1', 'response')
  const root = turn('c1', 'question', [agent])
  assert.deepEqual(responseOptions(respond([root], agent)), [])
})

test('answers use the saved challenge values and whole words', () => {
  assert.equal(matchesAnswer('Very frustrated!', 'frustrated'), true)
  assert.equal(
    matchesAnswer('I will reset the customer’s password.', 'reset password'),
    true,
  )
  assert.equal(
    matchesAnswer('Freeze the card and open a fraud claim.', 'reset password'),
    false,
  )
  assert.equal(matchesAnswer('unfrustrated', 'frustrated'), false)
  assert.equal(matchesAnswer('anything', ''), false)
})
