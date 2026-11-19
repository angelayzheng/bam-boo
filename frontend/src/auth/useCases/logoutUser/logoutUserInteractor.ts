import type { LogoutGateway } from '../../boundaries/dataAccessInterfaces'
import type {
  LogoutUserInputBoundary,
  LogoutUserInputData,
  LogoutUserOutputBoundary,
} from './logoutUserBoundaries'

export class LogoutUserInteractor implements LogoutUserInputBoundary {
  private readonly gateway: LogoutGateway
  private readonly output: LogoutUserOutputBoundary

  constructor(gateway: LogoutGateway, output: LogoutUserOutputBoundary) {
    this.gateway = gateway
    this.output = output
  }

  async execute(input: LogoutUserInputData): Promise<void> {
    if (input.signal?.aborted) return
    try {
      await this.gateway.logout(input.signal)
      if (input.signal?.aborted) return
      this.output.present({ status: 'ready' })
    } catch (error) {
      if (input.signal?.aborted) return
      this.output.present({
        status: 'error',
        message:
          error instanceof Error
            ? error.message
            : 'Could not log out. Please try again.',
      })
    }
  }
}
