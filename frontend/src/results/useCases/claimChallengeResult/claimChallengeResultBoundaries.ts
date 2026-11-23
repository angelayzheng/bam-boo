import type { AuthUser, ResultData } from '../../../entities/types'

export interface ClaimChallengeResultInputData {
  result: ResultData
  user: AuthUser | null
  sessionLoading: boolean
  signal: AbortSignal
}

export type ClaimChallengeResultOutputData =
  | {
      status:
        | 'checking'
        | 'guest'
        | 'saving'
        | 'other-account'
        | 'invalid'
        | 'unauthorized'
    }
  | { status: 'saved'; result: ResultData; claimed: boolean }
  | { status: 'error'; message: string }

export interface ClaimChallengeResultInputBoundary {
  execute(input: ClaimChallengeResultInputData): Promise<void>
}

export interface ClaimChallengeResultOutputBoundary {
  present(output: ClaimChallengeResultOutputData): void
}
