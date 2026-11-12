import type { ChallengeSession } from '../../entities/challengeSession.ts'
import type { SessionStore } from '../sessionStore.ts'
import type {
  SubmitToneInputBoundary,
  SubmitToneInputData,
  ToneInputData,
} from './submitToneBoundaries'
import type { ChallengeOutputBoundary } from '../../boundaries/challengeOutputBoundary'
import type { Clock, ToneGateway } from '../../boundaries/dataAccessInterfaces'

export class SubmitToneInteractor implements SubmitToneInputBoundary {
  private readonly store: SessionStore
  private readonly gateway: ToneGateway
  private readonly output: ChallengeOutputBoundary
  private readonly clock: Clock

  constructor(
    store: SessionStore,
    gateway: ToneGateway,
    output: ChallengeOutputBoundary,
    clock: Clock,
  ) {
    this.store = store
    this.gateway = gateway
    this.output = output
    this.clock = clock
  }

  setTone(input: ToneInputData): void {
    const session = this.store.get()
    if (!session) return
    session.changeTone(input.answer)
    this.present(session)
  }

  async execute(input: SubmitToneInputData): Promise<void> {
    const session = this.store.get()
    if (!session || session.snapshot().tonePending) return
    session.changeTone(input.answer)
    session.beginToneSubmission()
    this.present(session)
    const elapsed = Math.max(
      1,
      Math.round((this.clock.now() - session.startedAt) / 1000),
    )
    try {
      const correct = await this.gateway.score(
        session.snapshot().tone,
        session.challenge.slug,
        input.signal,
      )
      if (input.signal.aborted) return
      session.recordToneResult(correct, elapsed)
      this.present(session)
    } catch (error) {
      if (!input.signal.aborted) {
        session.recordToneError(
          error instanceof Error
            ? error.message
            : 'Tone scoring failed. Please try again.',
        )
        this.present(session)
      }
    }
  }

  private present(session: ChallengeSession): void {
    this.output.present({
      status: 'ready',
      challenge: session.challenge,
      session: session.snapshot(),
    })
  }
}
