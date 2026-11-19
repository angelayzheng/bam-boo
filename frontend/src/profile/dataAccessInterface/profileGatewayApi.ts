import type {
  ProfileGateway,
  UserProfileData,
} from '../boundaries/dataAccessInterfaces'

function isScoreRecord(value: unknown): value is Record<string, number> {
  if (typeof value !== 'object' || value === null || Array.isArray(value)) {
    return false
  }
  return Object.values(value).every(
    (score) => typeof score === 'number' && Number.isFinite(score),
  )
}

function parseProfile(value: unknown): UserProfileData {
  if (typeof value !== 'object' || value === null) {
    throw new Error('Your profile returned an unexpected format.')
  }
  const record = value as {
    user_id?: unknown
    username?: unknown
    avatar?: unknown
    total_score?: unknown
    completed_challenges?: unknown
    scores?: unknown
  }
  if (
    typeof record.user_id !== 'number' ||
    typeof record.username !== 'string' ||
    typeof record.avatar !== 'string' ||
    typeof record.total_score !== 'number' ||
    !Number.isFinite(record.total_score) ||
    typeof record.completed_challenges !== 'number' ||
    !isScoreRecord(record.scores)
  ) {
    throw new Error('Your profile returned an unexpected format.')
  }
  return {
    userId: record.user_id,
    username: record.username,
    avatar: record.avatar,
    totalScore: record.total_score,
    completedChallenges: record.completed_challenges,
    scores: record.scores,
  }
}

async function loadProfile(
  userId: number,
  signal: AbortSignal,
): Promise<UserProfileData> {
  const response = await fetch(`/api/users/${userId}/profile/`, {
    credentials: 'same-origin',
    cache: 'no-store',
    signal,
  })
  if (
    !response.ok ||
    !response.headers.get('content-type')?.includes('application/json')
  ) {
    throw new Error(
      'Could not load your profile. Check that the Django backend is running.',
    )
  }
  return parseProfile(await response.json())
}

export const profileGateway: ProfileGateway = {
  loadProfile,
}
