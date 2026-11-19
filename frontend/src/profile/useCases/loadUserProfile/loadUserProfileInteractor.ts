import { buildUserProfileProgress } from '../../../entities/userProfileProgress.ts'
import type { ProfileGateway } from '../../boundaries/dataAccessInterfaces'
import type {
  LoadUserProfileInputBoundary,
  LoadUserProfileInputData,
  LoadUserProfileOutputBoundary,
} from './loadUserProfileBoundaries'

export class LoadUserProfileInteractor implements LoadUserProfileInputBoundary {
  private readonly gateway: ProfileGateway
  private readonly output: LoadUserProfileOutputBoundary

  constructor(gateway: ProfileGateway, output: LoadUserProfileOutputBoundary) {
    this.gateway = gateway
    this.output = output
  }

  async execute(input: LoadUserProfileInputData): Promise<void> {
    if (input.signal.aborted) return
    try {
      const profile = await this.gateway.loadProfile(input.userId, input.signal)
      if (input.signal.aborted) return
      this.output.present({
        status: 'ready',
        profile,
        progress: buildUserProfileProgress(profile, input.summaries),
      })
    } catch (error) {
      if (input.signal.aborted) return
      this.output.present({
        status: 'error',
        message:
          error instanceof Error
            ? error.message
            : 'Could not load your profile.',
      })
    }
  }
}
