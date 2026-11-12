import type { ConversationNode } from './types.ts'

export function responseOptions(path: ConversationNode[]): ConversationNode[] {
  const current = path.at(-1)
  return current?.type === 'question' ? current.children : []
}

export function respond(
  path: ConversationNode[],
  response: ConversationNode,
): ConversationNode[] {
  if (!responseOptions(path).includes(response)) {
    throw new Error('Choose a response from the current conversation turn.')
  }
  // The recorded demo has one customer follow-up for each agent response.
  const customer = response.children[0]
  return [...path, response, ...(customer ? [customer] : [])]
}

export function matchesAnswer(answer: string, expected: string): boolean {
  const words: string[] = answer.toLowerCase().match(/[a-z0-9]+/g) ?? []
  const expectedWords: string[] =
    expected.toLowerCase().match(/[a-z0-9]+/g) ?? []
  return (
    expectedWords.length > 0 &&
    expectedWords.every((word) => words.includes(word))
  )
}
