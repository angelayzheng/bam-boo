import type { SignupGroupGateway } from '../../boundaries/dataAccessInterfaces'
import type {
  LoadSignupGroupsInputBoundary,
  LoadSignupGroupsInputData,
  LoadSignupGroupsOutputBoundary,
} from './loadSignupGroupsBoundaries'

export class LoadSignupGroupsInteractor implements LoadSignupGroupsInputBoundary {
  private readonly gateway: SignupGroupGateway
  private readonly output: LoadSignupGroupsOutputBoundary

  constructor(
    gateway: SignupGroupGateway,
    output: LoadSignupGroupsOutputBoundary,
  ) {
    this.gateway = gateway
    this.output = output
  }

  async execute(input: LoadSignupGroupsInputData): Promise<void> {
    if (input.signal.aborted) return
    try {
      const groups = await this.gateway.loadGroups(input.signal)
      if (input.signal.aborted) return
      this.output.present({ status: 'ready', groups })
    } catch (error) {
      if (input.signal.aborted) return
      this.output.present({
        status: 'error',
        message:
          error instanceof Error
            ? error.message
            : 'Could not load groups. Make sure the backend is running, then try again.',
      })
    }
  }
}
