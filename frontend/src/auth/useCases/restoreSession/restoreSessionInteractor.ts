import type { SessionGateway } from '../../boundaries/dataAccessInterfaces'
import type {
  RestoreSessionInputBoundary,
  RestoreSessionInputData,
  RestoreSessionOutputBoundary,
} from './restoreSessionBoundaries'

export class RestoreSessionInteractor implements RestoreSessionInputBoundary {
  private readonly gateway: SessionGateway
  private readonly output: RestoreSessionOutputBoundary

  constructor(gateway: SessionGateway, output: RestoreSessionOutputBoundary) {
    this.gateway = gateway
    this.output = output
  }

  async execute(input: RestoreSessionInputData): Promise<void> {
    if (input.signal.aborted) return
    try {
      const user = await this.gateway.restoreSession(input.signal)
      if (input.signal.aborted) return
      this.output.present({ status: 'ready', user })
    } catch (error) {
      if (input.signal.aborted) return
      this.output.present({
        status: 'error',
        message:
          error instanceof Error
            ? error.message
            : 'Could not check your account.',
      })
    }
  }
}
