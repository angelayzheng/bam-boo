import type {
  HomeProfileGateway,
  HomeProgress,
} from '../boundaries/dataAccessInterfaces'

function isScoreRecord(value: unknown): value is Record<string, number> {
  if (typeof value !== 'object' || value === null || Array.isArray(value)) {
    return false
  }
  return Object.values(value).every(
    (score) => typeof score === 'number' && Number.isFinite(score),
  )
}

function isStringArray(value: unknown): value is string[] {
  return (
    Array.isArray(value) && value.every((entry) => typeof entry === 'string')
  )
}

async function loadProgress(
  username: string,
  signal: AbortSignal,
): Promise<HomeProgress> {
  const response = await fetch(`/api/users/${encodeURIComponent(username)}/`, {
    credentials: 'same-origin',
    cache: 'no-store',
    signal,
  })
  if (
    !response.ok ||
    !response.headers.get('content-type')?.includes('application/json')
  ) {
    throw new Error(
      'Could not load your progress. Check that the Django backend is running.',
    )
  }
  const data: unknown = await response.json()
  if (typeof data !== 'object' || data === null) {
    throw new Error('Your progress returned an unexpected format.')
  }
  const payload = data as {
    challenge_scores?: unknown
    login_days?: unknown
  }
  if (
    !isScoreRecord(payload.challenge_scores) ||
    !isStringArray(payload.login_days)
  ) {
    throw new Error('Your progress returned an unexpected format.')
  }
  return {
    scores: payload.challenge_scores,
    loginDays: payload.login_days,
  }
}

export const profileApi: HomeProfileGateway = {
  loadProgress,
}
