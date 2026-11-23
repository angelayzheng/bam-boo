import type { ResultData } from '../../entities/types'
import type { SessionState } from '../../entities/challengeSession'

export type ChallengeOutputData =
  | { status: 'loading' }
  | { status: 'error'; message: string }
  | { status: 'ready'; session: SessionState }
  | {
      status: 'complete'
      session: SessionState
      result: ResultData
    }

export interface ChallengeOutputBoundary {
  present(output: ChallengeOutputData): void
}
