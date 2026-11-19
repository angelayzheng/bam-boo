import type { UserProfileProgress } from '../../../entities/userProfileProgress'
import type { ChallengeSummary } from '../../../entities/types'
import type { UserProfileData } from '../../boundaries/dataAccessInterfaces'

export interface LoadUserProfileInputData {
  userId: number
  summaries: ChallengeSummary[]
  signal: AbortSignal
}

export type LoadUserProfileOutputData =
  | {
      status: 'ready'
      profile: UserProfileData
      progress: UserProfileProgress
    }
  | { status: 'error'; message: string }

export interface LoadUserProfileInputBoundary {
  execute(input: LoadUserProfileInputData): Promise<void>
}

export interface LoadUserProfileOutputBoundary {
  present(output: LoadUserProfileOutputData): void
}
