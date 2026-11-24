import type {
  AttemptSnapshot,
  AttemptStatus,
  AttemptTurn,
  ChallengeSummary,
} from '../../entities/types'
import {
  ApiError,
  getJson,
  postJson,
} from '../../dataAccessInterface/httpClient.ts'
import type { AttemptGateway } from '../boundaries/dataAccessInterfaces'

const loadFallback =
  'Could not load the challenge. Check that the Django backend is running.'
const transitionFallback =
  'The challenge could not be updated. Please try again.'

interface ApiTurn {
  id: string
  type: 'question' | 'response'
  transcript_url: string
  audio_url: string
}

interface ApiChoice extends ApiTurn {
  choice_id: string
}

interface ApiSnapshot {
  attempt_id: string
  stage: AttemptStatus
  challenge: ChallengeSummary
  opening: ApiTurn
  conversation: ApiTurn[]
  choices: ApiChoice[]
  tone_correct: boolean | null
  tone_time: number | null
  tone_speed_correct: boolean | null
  tone_similarity?: number | null
  action_correct?: boolean | null
  score?: number | null
  required_action?: string | null
  completed_at?: string | null
  user_id?: number | null
  saved?: boolean
}

function mediaUrl(value: string): string {
  return new URL(value, `${window.location.origin}/`).href
}

async function loadTranscript(
  url: string,
  signal: AbortSignal,
): Promise<string> {
  const response = await fetch(url, { signal })
  if (
    !response.ok ||
    !response.headers.get('content-type')?.includes('text/plain')
  ) {
    throw new Error(
      'The recording transcript is missing. Import the challenge package and try again.',
    )
  }
  return (await response.text()).trim()
}

async function hydrateTurn(
  node: ApiTurn,
  signal: AbortSignal,
  transcripts: Map<string, Promise<string>>,
): Promise<AttemptTurn> {
  const transcriptUrl = mediaUrl(node.transcript_url)
  let transcript = transcripts.get(transcriptUrl)
  if (!transcript) {
    transcript = loadTranscript(transcriptUrl, signal)
    transcripts.set(transcriptUrl, transcript)
  }
  return {
    id: node.id,
    type: node.type,
    transcriptUrl,
    audioUrl: mediaUrl(node.audio_url),
    text: await transcript,
  }
}

async function hydrateSnapshot(
  raw: ApiSnapshot,
  signal: AbortSignal,
): Promise<AttemptSnapshot> {
  if (
    typeof raw.attempt_id !== 'string' ||
    !raw.challenge ||
    !raw.opening ||
    !Array.isArray(raw.conversation) ||
    !Array.isArray(raw.choices)
  ) {
    throw new Error('The challenge service returned an invalid attempt.')
  }
  const transcripts = new Map<string, Promise<string>>()
  const [opening, conversation, choices] = await Promise.all([
    hydrateTurn(raw.opening, signal, transcripts),
    Promise.all(
      raw.conversation.map((node) => hydrateTurn(node, signal, transcripts)),
    ),
    Promise.all(
      raw.choices.map(async (node) => ({
        ...(await hydrateTurn(node, signal, transcripts)),
        choiceId: node.choice_id,
      })),
    ),
  ])
  return {
    attemptId: raw.attempt_id,
    stage: raw.stage,
    challenge: raw.challenge,
    opening,
    conversation,
    choices,
    toneCorrect: raw.tone_correct ?? null,
    toneTime: raw.tone_time ?? null,
    toneSpeedCorrect: raw.tone_speed_correct ?? null,
    toneSimilarity: raw.tone_similarity ?? null,
    actionCorrect: raw.action_correct ?? null,
    score: raw.score ?? null,
    requiredAction: raw.required_action ?? null,
    completedAt: raw.completed_at ?? null,
    userId: raw.user_id ?? null,
    saved: raw.saved === true,
  }
}

function fail(
  error: unknown,
  fallback: string,
  statusMessages: Partial<Record<number, string>> = {},
): never {
  if (error instanceof ApiError) {
    throw new Error(statusMessages[error.status] ?? error.message)
  }
  if (error instanceof Error) throw new Error(error.message || fallback)
  throw new Error(fallback)
}

async function start(
  slug: string,
  signal: AbortSignal,
): Promise<AttemptSnapshot> {
  try {
    const raw = await postJson<ApiSnapshot>(
      `/api/challenges/${encodeURIComponent(slug)}/attempts/`,
      {},
      signal,
      loadFallback,
    )
    const snapshot = await hydrateSnapshot(raw, signal)
    return snapshot
  } catch (error) {
    fail(error, loadFallback, {
      404: 'This challenge could not be found.',
      409: 'This challenge is not available to play.',
    })
  }
}

async function load(
  attemptId: string,
  signal: AbortSignal,
): Promise<AttemptSnapshot | null> {
  try {
    const raw = await getJson<ApiSnapshot>(
      `/api/attempts/${encodeURIComponent(attemptId)}/`,
      signal,
      loadFallback,
    )
    return await hydrateSnapshot(raw, signal)
  } catch (error) {
    if (
      error instanceof ApiError &&
      (error.status === 404 || error.status === 403)
    ) {
      return null
    }
    if (error instanceof Error) throw new Error(error.message || loadFallback)
    throw new Error(loadFallback)
  }
}

async function submitTone(
  attemptId: string,
  answer: string,
  signal: AbortSignal,
): Promise<AttemptSnapshot> {
  try {
    const raw = await postJson<ApiSnapshot>(
      `/api/attempts/${encodeURIComponent(attemptId)}/tone/`,
      { answer },
      signal,
      transitionFallback,
    )
    return await hydrateSnapshot(raw, signal)
  } catch (error) {
    fail(error, transitionFallback, {
      403: 'This attempt belongs to another account.',
      404: 'This attempt is no longer available. Reload the challenge.',
      409: 'This attempt has already moved on. Reload the challenge.',
      422: 'Tone not recognized. Try another word or phrase.',
      503: 'Tone scoring is unavailable. Please try again.',
    })
  }
}

async function chooseResponse(
  attemptId: string,
  choiceId: string,
  signal: AbortSignal,
): Promise<AttemptSnapshot> {
  try {
    const raw = await postJson<ApiSnapshot>(
      `/api/attempts/${encodeURIComponent(attemptId)}/choices/`,
      { choice_id: choiceId },
      signal,
      transitionFallback,
    )
    return await hydrateSnapshot(raw, signal)
  } catch (error) {
    fail(error, transitionFallback, {
      403: 'This attempt belongs to another account.',
      404: 'This attempt is no longer available.',
    })
  }
}

async function continueConversation(
  attemptId: string,
  signal: AbortSignal,
): Promise<AttemptSnapshot> {
  try {
    const raw = await postJson<ApiSnapshot>(
      `/api/attempts/${encodeURIComponent(attemptId)}/continue/`,
      {},
      signal,
      transitionFallback,
    )
    return await hydrateSnapshot(raw, signal)
  } catch (error) {
    fail(error, transitionFallback, {
      403: 'This attempt belongs to another account.',
      404: 'This attempt is no longer available.',
    })
  }
}

async function submitAction(
  attemptId: string,
  answer: string,
  signal: AbortSignal,
): Promise<AttemptSnapshot> {
  try {
    const raw = await postJson<ApiSnapshot>(
      `/api/attempts/${encodeURIComponent(attemptId)}/action/`,
      { answer },
      signal,
      transitionFallback,
    )
    return await hydrateSnapshot(raw, signal)
  } catch (error) {
    fail(error, transitionFallback, {
      403: 'This attempt belongs to another account.',
      404: 'This attempt is no longer available.',
      409: 'This attempt has already completed. Check your results.',
    })
  }
}

export const attemptApi: AttemptGateway = {
  start,
  load,
  submitTone,
  chooseResponse,
  continueConversation,
  submitAction,
}
