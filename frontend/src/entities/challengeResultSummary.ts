import type { AuthUser, ChallengeSummary, ResultData } from './types'

export type ClaimEligibility =
  'checking' | 'guest' | 'saved' | 'other-account' | 'invalid' | 'claimable'

export interface ResultOutcomes {
  tone: boolean
  speed: boolean
  action: boolean
  stars: number
}

function isChallengeSummary(value: unknown): value is ChallengeSummary {
  if (typeof value !== 'object' || value === null) return false
  const candidate = value as ChallengeSummary
  return (
    typeof candidate.name === 'string' &&
    typeof candidate.slug === 'string' &&
    typeof candidate.challenge_date === 'string' &&
    typeof candidate.difficulty === 'number' &&
    typeof candidate.category === 'string'
  )
}

export function parseChallengeResult(value: unknown): ResultData | null {
  if (typeof value !== 'object' || value === null) return null
  const candidate = value as Partial<ResultData>
  if (
    typeof candidate.attemptId !== 'string' ||
    !candidate.attemptId ||
    typeof candidate.completedAt !== 'string' ||
    !candidate.completedAt ||
    typeof candidate.toneCorrect !== 'boolean' ||
    typeof candidate.toneTime !== 'number' ||
    !Number.isFinite(candidate.toneTime) ||
    candidate.toneTime < 0 ||
    typeof candidate.toneSpeedCorrect !== 'boolean' ||
    typeof candidate.actionCorrect !== 'boolean' ||
    typeof candidate.score !== 'number' ||
    !Number.isInteger(candidate.score) ||
    candidate.score < 0 ||
    candidate.score > 3 ||
    typeof candidate.requiredAction !== 'string' ||
    !candidate.requiredAction ||
    !isChallengeSummary(candidate.challenge)
  ) {
    return null
  }
  const toneSimilarity =
    typeof candidate.toneSimilarity === 'number' &&
    Number.isFinite(candidate.toneSimilarity) &&
    candidate.toneSimilarity >= -1 &&
    candidate.toneSimilarity <= 1
      ? candidate.toneSimilarity
      : null
  const userId =
    typeof candidate.userId === 'number' &&
    Number.isInteger(candidate.userId) &&
    candidate.userId > 0
      ? candidate.userId
      : null
  return {
    attemptId: candidate.attemptId,
    challenge: {
      name: candidate.challenge.name,
      slug: candidate.challenge.slug,
      challenge_date: candidate.challenge.challenge_date,
      difficulty: candidate.challenge.difficulty,
      category: candidate.challenge.category,
    },
    completedAt: candidate.completedAt,
    toneCorrect: candidate.toneCorrect,
    toneTime: candidate.toneTime,
    toneSpeedCorrect: candidate.toneSpeedCorrect,
    toneSimilarity,
    actionCorrect: candidate.actionCorrect,
    score: candidate.score,
    requiredAction: candidate.requiredAction,
    userId,
    saved: candidate.saved === true,
  }
}

export function claimEligibility(
  result: ResultData,
  user: AuthUser | null,
  sessionLoading: boolean,
): ClaimEligibility {
  if (sessionLoading) return 'checking'
  if (!parseChallengeResult(result)) return 'invalid'
  if (!user) return 'guest'
  if (
    result.userId !== null &&
    result.userId !== undefined &&
    result.userId !== user.id
  ) {
    return 'other-account'
  }
  if (result.saved) return 'saved'
  return 'claimable'
}

export function markResultClaimed(
  result: ResultData,
  userId: number,
): ResultData {
  return { ...result, userId, saved: true }
}

export function resultOutcomes(result: ResultData): ResultOutcomes {
  return {
    tone: result.toneCorrect,
    speed: result.toneSpeedCorrect,
    action: result.actionCorrect,
    stars: result.score,
  }
}
