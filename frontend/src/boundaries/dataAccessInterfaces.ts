import type { Challenge, ChallengeSummary } from '../types'

export interface ToneGateway {
  score(answer: string, slug: string, signal: AbortSignal): Promise<boolean>
}

export interface ChallengeGateway {
  loadSummaries(signal: AbortSignal): Promise<ChallengeSummary[]>
  loadByDate(date: string, signal: AbortSignal): Promise<Challenge>
  loadDetail(slug: string, signal: AbortSignal): Promise<Challenge>
}

export interface Clock {
  now(): number
}

export interface IdGenerator {
  randomId(): string
}
