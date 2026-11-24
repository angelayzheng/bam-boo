import { ChallengeSession } from '../../../entities/challengeSession.ts'
import type { SessionStore } from '../sessionStore.ts'
import type {
  StartChallengeInputBoundary,
  StartChallengeInputData,
} from './startChallengeBoundaries'
import type { ChallengeOutputBoundary } from '../../boundaries/challengeOutputBoundary'
import type {
  AttemptGateway,
  AttemptStorage,
} from '../../boundaries/dataAccessInterfaces'

export class StartChallengeInteractor implements StartChallengeInputBoundary {
  private readonly gateway: AttemptGateway
  private readonly storage: AttemptStorage
  private readonly output: ChallengeOutputBoundary
  private readonly store: SessionStore

  constructor(
    gateway: AttemptGateway,
    storage: AttemptStorage,
    output: ChallengeOutputBoundary,
    store: SessionStore,
  ) {
    this.gateway = gateway
    this.storage = storage
    this.output = output
    this.store = store
  }

  async execute(input: StartChallengeInputData): Promise<void> {
    this.output.present({ status: 'loading' })
    try {
      const storedAttemptId = this.storage.load(input.slug)
      let snapshot = storedAttemptId
        ? await this.gateway.load(storedAttemptId, input.signal)
        : null
      if (input.signal.aborted) return

      if (snapshot?.stage === 'completed') {
        this.storage.clear(input.slug)
        snapshot = null
      }
      if (!snapshot) {
        snapshot = await this.gateway.start(input.slug, input.signal)
        if (input.signal.aborted) return
      }

      this.storage.save(input.slug, snapshot.attemptId)
      const session = new ChallengeSession(snapshot)
      this.store.set(session)
      this.output.present({ status: 'ready', session: session.snapshot() })
    } catch (error) {
      if (!input.signal.aborted) {
        this.output.present({
          status: 'error',
          message:
            error instanceof Error
              ? error.message
              : 'Could not start the challenge.',
        })
      }
    }
  }
}
