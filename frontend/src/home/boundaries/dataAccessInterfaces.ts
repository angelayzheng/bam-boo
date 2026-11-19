export interface HomeProgress {
  scores: Record<string, number>
  loginDays: string[]
}

export interface HomeProfileGateway {
  loadProgress(username: string, signal: AbortSignal): Promise<HomeProgress>
}

export interface LeaderboardEntry {
  userId: number
  username: string
  avatar: string
  totalScore: number
}

export interface LeaderboardGateway {
  loadLeaderboard(signal: AbortSignal): Promise<LeaderboardEntry[]>
}
