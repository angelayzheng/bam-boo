import type { ChallengeSummary } from './types'

export function selectHomeChallenge(
  summaries: ChallengeSummary[],
): ChallengeSummary | null {
  return (
    summaries.find(({ slug }) => slug === 'forgot-password-x3') ??
    summaries[0] ??
    null
  )
}
