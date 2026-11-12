import type { ChallengeSession } from '../../entities/challengeSession.ts'
import type { SessionStore } from '../sessionStore.ts'
import type {
  ActionInputData,
  CompleteChallengeInputBoundary,
} from './completeChallengeBoundaries'
import type { ChallengeOutputBoundary } from '../../boundaries/challengeOutputBoundary'
import type { Clock, IdGenerator } from '../../boundaries/dataAccessInterfaces'

export class CompleteChallengeInteractor implements CompleteChallengeInputBoundary {
  private readonly store: SessionStore
  private readonly output: ChallengeOutputBoundary
  private readonly ids: IdGenerator
  private readonly clock: Clock

  constructor(
    store: SessionStore,
    output: ChallengeOutputBoundary,
    ids: IdGenerator,
    clock: Clock,
  ) {
    this.store = store
    this.output = output
    this.ids = ids
    this.clock = clock
  }

  setAction(input: ActionInputData): void {
    const session = this.store.get()
    if (!session) return
    session.changeAction(input.action)
    this.present(session)
  }

  execute(): void {
    const session = this.store.get()
    if (!session) return
    const result = session.buildResult(
      this.ids.randomId(),
      new Date(this.clock.now()).toISOString(),
    )
    this.output.present({
      status: 'complete',
      challenge: session.challenge,
      session: session.snapshot(),
      result,
    })
  }

  private present(session: ChallengeSession): void {
    this.output.present({
      status: 'ready',
      challenge: session.challenge,
      session: session.snapshot(),
    })
  }
}
