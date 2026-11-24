import type { ResultData } from '../../entities/types'

export interface ResultClaimResponse {
  user_id: number
  username: string
  avatar: string
  total_score: number
  completed_challenges: number
  scores: Record<string, number>
  attempt: {
    attempt_id: string
    challenge_slug: string
    score: number
    completed_at: string
  }
}

export type ResultClaimFailureReason = 'unauthorized' | 'failed'

export class ResultClaimError extends Error {
  readonly reason: ResultClaimFailureReason

  constructor(message: string, reason: ResultClaimFailureReason) {
    super(message)
    this.reason = reason
  }
}

export interface ResultClaimGateway {
  claimAttempt(
    attemptId: string,
    challengeSlug: string,
    signal: AbortSignal,
  ): Promise<ResultClaimResponse>
}

export interface ResultStorage {
  load(): unknown | null
  save(result: ResultData): void
  clear(): void
}
