import type { LeaderboardEntry } from '../../boundaries/dataAccessInterfaces'

export interface LoadLeaderboardInputData {
  currentUserId: number | null
  signal: AbortSignal
}

export type LoadLeaderboardOutputData =
  | {
      status: 'ready'
      entries: LeaderboardEntry[]
      currentUserId: number | null
    }
  | { status: 'error'; message: string }

export interface LoadLeaderboardInputBoundary {
  execute(input: LoadLeaderboardInputData): Promise<void>
}

export interface LoadLeaderboardOutputBoundary {
  present(output: LoadLeaderboardOutputData): void
}
