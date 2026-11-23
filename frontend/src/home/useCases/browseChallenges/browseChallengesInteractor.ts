// Use case: fetch one month of calendar entries.
import type { HomeChallengeGateway } from '../../boundaries/dataAccessInterfaces'
import type {
  BrowseChallengesInputBoundary,
  BrowseChallengesInputData,
  BrowseChallengesOutputBoundary,
} from './browseChallengesBoundaries'

export class BrowseChallengesInteractor implements BrowseChallengesInputBoundary {
  private readonly gateway: HomeChallengeGateway
  private readonly output: BrowseChallengesOutputBoundary

  constructor(
    gateway: HomeChallengeGateway,
    output: BrowseChallengesOutputBoundary,
  ) {
    this.gateway = gateway
    this.output = output
  }

  async execute({ month, signal }: BrowseChallengesInputData): Promise<void> {
    if (signal.aborted) return
    if (month.month < 1 || month.month > 12) {
      this.output.present({
        status: 'error',
        month,
        message: 'Month must be between 1 and 12.',
        entries: [],
      })
      return
    }
    try {
      const entries = await this.gateway.browseChallenges(month, signal)
      if (signal.aborted) return
      this.output.present({ status: 'ready', month, entries })
    } catch (error) {
      if (signal.aborted) return
      this.output.present({
        status: 'error',
        month,
        message:
          error instanceof Error
            ? error.message
            : 'Could not load the calendar.',
        entries: [],
      })
    }
  }
}
