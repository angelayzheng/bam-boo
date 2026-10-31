import type { ResultData } from './types'

export interface AuthUser {
  id: number
  username: string
  email: string
}

export interface UserProfile {
  user_id: number
  username: string
  avatar: string
  total_score: number
  completed_challenges: number
  scores: Record<string, number>
}

export interface Credentials {
  username: string
  password: string
  email?: string
  group_id?: number | null
}

export interface SignupGroup {
  id: number
  name: string
}

export async function loadSignupGroups(
  signal: AbortSignal,
): Promise<SignupGroup[]> {
  const response = await fetch('/api/users/groups/', {
    credentials: 'same-origin',
    cache: 'no-store',
    signal,
  })
  return (await readResponse<{ groups: SignupGroup[] }>(response)).groups
}

export interface ScoreSaveResponse extends UserProfile {
  attempt: {
    id: number
    attempt_id: string
    challenge_id: number
    score: number
    completed_at: string
    received_at: string
  }
}

const basePath = '/api/users/auth/'

export class ApiError extends Error {
  status: number

  constructor(message: string, status: number) {
    super(message)
    this.status = status
  }
}

async function readResponse<T>(response: Response): Promise<T> {
  if (!response.headers.get('content-type')?.includes('application/json')) {
    throw new Error(
      response.status === 403
        ? 'Your security token expired. Please try again.'
        : 'Could not connect to your account. Please try again.',
    )
  }
  const data = await response.json()
  if (!response.ok) {
    const messages = data.errors
      ? Object.values(data.errors).flat().join(' ')
      : data.detail
    throw new ApiError(
      messages || 'Your request failed. Please try again.',
      response.status,
    )
  }
  return data as T
}

export async function getCurrentUser(
  signal: AbortSignal,
): Promise<AuthUser | null> {
  const response = await fetch(`${basePath}me/`, {
    credentials: 'same-origin',
    cache: 'no-store',
    signal,
  })
  if (response.status === 401) return null
  return (await readResponse<{ user: AuthUser }>(response)).user
}

async function postJson<T>(
  path: string,
  payload: object = {},
  signal?: AbortSignal,
): Promise<T> {
  // Fetch the current token for every mutation, including after login rotation.
  const tokenResponse = await fetch(`${basePath}csrf/`, {
    credentials: 'same-origin',
    cache: 'no-store',
    signal,
  })
  const { csrfToken } = await readResponse<{ csrfToken: string }>(tokenResponse)
  const response = await fetch(path, {
    method: 'POST',
    credentials: 'same-origin',
    signal,
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': csrfToken,
    },
    body: JSON.stringify(payload),
  })
  return readResponse<T>(response)
}

export async function signIn(
  action: 'login' | 'signup',
  credentials: Credentials,
  signal?: AbortSignal,
): Promise<AuthUser> {
  return (
    await postJson<{ user: AuthUser }>(
      `${basePath}${action}/`,
      credentials,
      signal,
    )
  ).user
}

export async function signOut(): Promise<void> {
  await postJson(`${basePath}logout/`)
}

export async function saveChallengeResult(
  result: ResultData,
  signal: AbortSignal,
): Promise<ScoreSaveResponse> {
  return postJson<ScoreSaveResponse>(
    `/api/users/me/scores/${result.challengeId}/`,
    {
      tone_correct: result.toneCorrect,
      tone_time: result.toneTime,
      action_correct: result.actionCorrect,
      attempt_id: result.attemptId,
      completed_at: result.completedAt,
    },
    signal,
  )
}

export async function loadProfile(
  userId: number,
  signal: AbortSignal,
): Promise<UserProfile> {
  const response = await fetch(`/api/users/${userId}/profile/`, {
    credentials: 'same-origin',
    cache: 'no-store',
    signal,
  })
  return readResponse<UserProfile>(response)
}
