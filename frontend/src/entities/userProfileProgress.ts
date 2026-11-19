import type { ChallengeSummary } from './types'

export interface UserProfileProgressInput {
  totalScore: number
  completedChallenges: number
  scores: Record<string, number>
}

export interface ProfileScoreRow {
  slug: string
  name: string
  challengeDate: string | null
  score: number
}

export interface UserProfileProgress {
  totalScore: number
  completedChallenges: number
  scores: ProfileScoreRow[]
}

export function buildUserProfileProgress(
  input: UserProfileProgressInput,
  summaries: ChallengeSummary[],
): UserProfileProgress {
  const summaryBySlug = new Map(
    summaries.map((summary) => [summary.slug, summary]),
  )
  return {
    totalScore: input.totalScore,
    completedChallenges: input.completedChallenges,
    scores: Object.entries(input.scores).map(([slug, score]) => {
      const summary = summaryBySlug.get(slug)
      return {
        slug,
        name: summary?.name ?? `Challenge ${slug}`,
        challengeDate: summary?.challenge_date ?? null,
        score,
      }
    }),
  }
}
