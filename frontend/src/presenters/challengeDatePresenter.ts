import type { ChallengeSummary } from '../types'

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
