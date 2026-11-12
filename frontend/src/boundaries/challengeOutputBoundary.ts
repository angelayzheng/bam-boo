import type { Challenge, ResultData } from '../types'
import type { SessionState } from '../entities/challengeSession'

export type ChallengeOutputData =
  | { status: 'loading' }
  | { status: 'error'; message: string }
  | { status: 'ready'; challenge: Challenge; session: SessionState }
  | {
      status: 'complete'
      challenge: Challenge
      session: SessionState
      result: ResultData
    }

export interface ChallengeOutputBoundary {
  present(output: ChallengeOutputData): void
}
