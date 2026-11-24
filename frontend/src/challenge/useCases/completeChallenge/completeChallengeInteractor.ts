import type { ChallengeSession } from '../../../entities/challengeSession.ts'
import type { AttemptSnapshot } from '../../../entities/types'
import type { SessionStore } from '../sessionStore.ts'
import type {
  ActionInputData,
  CompleteChallengeInputBoundary,
  CompleteChallengeInputData,
} from './completeChallengeBoundaries'
import type { ChallengeOutputBoundary } from '../../boundaries/challengeOutputBoundary'
import type {
  AttemptGateway,
  AttemptStorage,
} from '../../boundaries/dataAccessInterfaces'

export class CompleteChallengeInteractor implements CompleteChallengeInputBoundary {
  private readonly store: SessionStore
  private readonly gateway: AttemptGateway
  private readonly output: ChallengeOutputBoundary
  private readonly storage: AttemptStorage

  constructor(
    store: SessionStore,
    gateway: AttemptGateway,
    output: ChallengeOutputBoundary,
    storage: AttemptStorage,
  ) {
    this.store = store
    this.gateway = gateway
    this.output = output
    this.storage = storage
  }

  setAction(input: ActionInputData): void {
    const session = this.store.get()
    if (!session) return
    session.changeAction(input.action)
    this.present(session)
  }

  async execute(input: CompleteChallengeInputData): Promise<void> {
    const session = this.store.get()
    if (!session) return
    const state = session.snapshot()
    if (
      state.actionPending ||
      state.stage !== 'action' ||
      !state.nextAction.trim()
    ) {
      return
    }

    session.beginActionSubmission()
    this.present(session)
    try {
      const snapshot = await this.gateway.submitAction(
        state.attemptId,
        state.nextAction,
        input.signal,
      )
      if (input.signal.aborted) return
      this.complete(session, snapshot)
    } catch (error) {
      if (input.signal.aborted) return

      // The server may have committed the action even if its response was lost.
      // Reload the run before showing a retry error so completed work reaches results.
      try {
        const snapshot = await this.gateway.load(state.attemptId, input.signal)
        if (input.signal.aborted) return
        if (snapshot?.stage === 'completed') {
          this.complete(session, snapshot)
          return
        }
      } catch {
        if (input.signal.aborted) return
      }

      session.recordActionError(
        error instanceof Error
          ? error.message
          : 'Could not submit your action. Please try again.',
      )
      this.present(session)
    }
  }

  private complete(session: ChallengeSession, snapshot: AttemptSnapshot): void {
    session.recordActionResult(snapshot)
    const result = session.buildResult()
    this.storage.clear(session.snapshot().challenge.slug)
    this.output.present({
      status: 'complete',
      session: session.snapshot(),
      result,
    })
  }

  private present(session: ChallengeSession): void {
    this.output.present({ status: 'ready', session: session.snapshot() })
  }
}
