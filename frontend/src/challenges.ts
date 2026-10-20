import type { Challenge, ChallengeSummary, ConversationNode } from './types'

// Vite proxies these same-origin requests to Django in local development.
async function getJson<T>(path: string, signal: AbortSignal): Promise<T> {
  const response = await fetch(path, { signal })
  if (
    !response.ok ||
    !response.headers.get('content-type')?.includes('application/json')
  ) {
    throw new Error(
      'Could not load the recording. Check that the Django backend is running.',
    )
  }
  return response.json() as Promise<T>
}

async function loadTurn(
  node: ConversationNode,
  signal: AbortSignal,
): Promise<ConversationNode> {
  const transcriptUrl = new URL(
    node.transcript_url,
    window.location.origin + '/',
  ).href
  const audioUrl = new URL(node.audio_url, window.location.origin + '/').href
  const [response, children] = await Promise.all([
    fetch(transcriptUrl, { signal }),
    Promise.all(node.children.map((child) => loadTurn(child, signal))),
  ])
  if (
    !response.ok ||
    !response.headers.get('content-type')?.includes('text/plain')
  ) {
    throw new Error(
      'The recording transcript is missing. Run the demo seed command in the setup guide.',
    )
  }
  return {
    ...node,
    text: (await response.text()).trim(),
    audio_url: audioUrl,
    children,
  }
}

export async function loadChallenge(signal: AbortSignal): Promise<Challenge> {
  const { challenges } = await getJson<{ challenges: ChallengeSummary[] }>(
    '/api/challenges/',
    signal,
  )
  const selected =
    challenges.find(({ slug }) => slug === 'forgot-password-x3') ??
    challenges[0]
  if (!selected) {
    throw new Error(
      'No recordings are available. Run the demo seed command in the setup guide.',
    )
  }
  const challenge = await getJson<Challenge>(
    `/api/challenges/${selected.id}/`,
    signal,
  )
  if (challenge.conversation_tree.type !== 'question') {
    throw new Error(
      'This recording has no conversation tree. Run the demo seed command in the setup guide.',
    )
  }
  return {
    ...challenge,
    conversation_tree: await loadTurn(challenge.conversation_tree, signal),
  }
}

export function challengeDate(challenge: ChallengeSummary): Date {
  return new Date(`${challenge.challenge_date}T00:00:00`)
}

export function challengeDateLabel(challenge: ChallengeSummary): string {
  return new Intl.DateTimeFormat('en-CA', {
    weekday: 'long',
    month: 'long',
    day: 'numeric',
    year: 'numeric',
  }).format(challengeDate(challenge))
}
