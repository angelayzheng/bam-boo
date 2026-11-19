import type { LeaderboardGateway } from '../../boundaries/dataAccessInterfaces'
import type {
  LoadLeaderboardInputBoundary,
  LoadLeaderboardInputData,
  LoadLeaderboardOutputBoundary,
} from './loadLeaderboardBoundaries'

export class LoadLeaderboardInteractor implements LoadLeaderboardInputBoundary {
  private readonly gateway: LeaderboardGateway
  private readonly output: LoadLeaderboardOutputBoundary

  constructor(
    gateway: LeaderboardGateway,
    output: LoadLeaderboardOutputBoundary,
  ) {
    this.gateway = gateway
    this.output = output
  }

  async execute(input: LoadLeaderboardInputData): Promise<void> {
    if (input.signal.aborted) return
    try {
      const entries = await this.gateway.loadLeaderboard(input.signal)
      if (input.signal.aborted) return
      this.output.present({
        status: 'ready',
        entries,
        currentUserId: input.currentUserId,
      })
    } catch (error) {
      if (input.signal.aborted) return
      this.output.present({
        status: 'error',
        message:
          error instanceof Error
            ? error.message
            : 'Could not load the leaderboard.',
      })
    }
  }
}
