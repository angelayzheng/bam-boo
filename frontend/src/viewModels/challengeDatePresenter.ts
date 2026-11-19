import type { ChallengeSummary } from '../entities/types'

export function challengeDate(challenge: ChallengeSummary): Date {
  return new Date(`${challenge.challenge_date}T00:00:00`)
}

export function formatChallengeDate(value: string): string {
  return new Intl.DateTimeFormat('en-CA', {
    weekday: 'long',
    month: 'long',
    day: 'numeric',
    year: 'numeric',
  }).format(new Date(`${value}T00:00:00`))
}

export function challengeDateLabel(challenge: ChallengeSummary): string {
  return formatChallengeDate(challenge.challenge_date)
}
