import type {
  LeaderboardEntry,
  LeaderboardGateway,
} from '../boundaries/dataAccessInterfaces'

function parseEntry(value: unknown): LeaderboardEntry {
  if (typeof value !== 'object' || value === null) {
    throw new Error('The leaderboard returned an unexpected format.')
  }
  const record = value as {
    user_id?: unknown
    username?: unknown
    avatar?: unknown
    total_score?: unknown
  }
  if (
    typeof record.user_id !== 'number' ||
    typeof record.username !== 'string' ||
    typeof record.total_score !== 'number' ||
    !Number.isFinite(record.total_score)
  ) {
    throw new Error('The leaderboard returned an unexpected format.')
  }
  return {
    userId: record.user_id,
    username: record.username,
    avatar: typeof record.avatar === 'string' ? record.avatar : '',
    totalScore: record.total_score,
  }
}

async function loadLeaderboard(
  signal: AbortSignal,
): Promise<LeaderboardEntry[]> {
  const response = await fetch('/api/users/leaderboard/', {
    credentials: 'same-origin',
    cache: 'no-store',
    signal,
  })
  if (
    !response.ok ||
    !response.headers.get('content-type')?.includes('application/json')
  ) {
    throw new Error(
      'Could not load the leaderboard. Check that the Django backend is running.',
    )
  }
  const data: unknown = await response.json()
  if (typeof data !== 'object' || data === null) {
    throw new Error('The leaderboard returned an unexpected format.')
  }
  const payload = data as { leaderboard?: unknown }
  if (!Array.isArray(payload.leaderboard)) {
    throw new Error('The leaderboard returned an unexpected format.')
  }
  return payload.leaderboard.map(parseEntry)
}

export const leaderboardApi: LeaderboardGateway = {
  loadLeaderboard,
}
