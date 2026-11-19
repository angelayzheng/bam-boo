import type { ChallengeSummary } from '../../../entities/types'

export interface LoadTodayChallengeInputData {
  summaries: ChallengeSummary[]
}

export interface LoadTodayChallengeOutputData {
  challenge: ChallengeSummary | null
}

export interface LoadTodayChallengeInputBoundary {
  execute(input: LoadTodayChallengeInputData): void
}

export interface LoadTodayChallengeOutputBoundary {
  present(output: LoadTodayChallengeOutputData): void
}
