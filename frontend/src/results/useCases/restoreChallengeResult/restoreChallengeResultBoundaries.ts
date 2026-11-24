import type { ResultData } from '../../../entities/types'

export interface RestoreChallengeResultInputData {
  slug: string | null
  seed?: ResultData | null
}

export type RestoreChallengeResultOutputData =
  | { status: 'ready'; result: ResultData }
  | { status: 'unavailable'; message: string }

export interface RestoreChallengeResultInputBoundary {
  execute(input: RestoreChallengeResultInputData): void
}

export interface RestoreChallengeResultOutputBoundary {
  present(output: RestoreChallengeResultOutputData): void
}
