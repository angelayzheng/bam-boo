import { ChallengeSession } from '../../entities/challengeSession.ts'
import type { SessionStore } from '../sessionStore.ts'
import type {
  StartChallengeInputBoundary,
  StartChallengeInputData,
} from './startChallengeBoundaries'
import type { ChallengeOutputBoundary } from '../../boundaries/challengeOutputBoundary'
import type {
  ChallengeGateway,
  Clock,
} from '../../boundaries/dataAccessInterfaces'

export class StartChallengeInteractor implements StartChallengeInputBoundary {
  private readonly gateway: ChallengeGateway
  private readonly output: ChallengeOutputBoundary
  private readonly clock: Clock
  private readonly store: SessionStore

  constructor(
    gateway: ChallengeGateway,
    output: ChallengeOutputBoundary,
    clock: Clock,
    store: SessionStore,
  ) {
    this.gateway = gateway
    this.output = output
    this.clock = clock
    this.store = store
  }

  async execute(input: StartChallengeInputData): Promise<void> {
    this.output.present({ status: 'loading' })
    try {
      const challenge = await this.gateway.loadByDate(input.date, input.signal)
      if (input.signal.aborted) return
      const session = new ChallengeSession(challenge, this.clock.now())
      this.store.set(session)
      this.output.present({
        status: 'ready',
        challenge,
        session: session.snapshot(),
      })
    } catch (error) {
      if (!input.signal.aborted) {
        this.output.present({
          status: 'error',
          message:
            error instanceof Error
              ? error.message
              : 'Could not load the recording.',
        })
      }
    }
  }
}
