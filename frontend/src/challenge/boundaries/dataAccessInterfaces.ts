import type { Challenge, ChallengeSummary } from '../../entities/types'

export interface ToneGateway {
  score(answer: string, slug: string, signal: AbortSignal): Promise<boolean>
}

export interface ChallengeGateway {
  loadSummaries(signal: AbortSignal): Promise<ChallengeSummary[]>
  loadDetail(slug: string, signal: AbortSignal): Promise<Challenge>
}

export interface Clock {
  now(): number
}

export interface IdGenerator {
  randomId(): string
}
