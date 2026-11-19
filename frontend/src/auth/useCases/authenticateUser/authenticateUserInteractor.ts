import type { AuthenticationGateway } from '../../boundaries/dataAccessInterfaces'
import type {
  AuthenticateUserInputBoundary,
  AuthenticateUserInputData,
  AuthenticateUserOutputBoundary,
} from './authenticateUserBoundaries'

export class AuthenticateUserInteractor implements AuthenticateUserInputBoundary {
  private readonly gateway: AuthenticationGateway
  private readonly output: AuthenticateUserOutputBoundary

  constructor(
    gateway: AuthenticationGateway,
    output: AuthenticateUserOutputBoundary,
  ) {
    this.gateway = gateway
    this.output = output
  }

  async execute(input: AuthenticateUserInputData): Promise<void> {
    if (input.signal.aborted) return
    try {
      const user = await this.gateway.authenticate(
        input.action,
        input.credentials,
        input.signal,
      )
      if (input.signal.aborted) return
      this.output.present({ status: 'ready', user })
    } catch (error) {
      if (input.signal.aborted) return
      this.output.present({
        status: 'error',
        message:
          error instanceof Error
            ? error.message
            : 'Could not sign in. Please try again.',
      })
    }
  }
}
