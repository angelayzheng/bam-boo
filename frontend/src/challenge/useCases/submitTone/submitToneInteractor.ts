import type { ChallengeSession } from '../../../entities/challengeSession.ts'
import type { SessionStore } from '../sessionStore.ts'
import type {
  SubmitToneInputBoundary,
  SubmitToneInputData,
  ToneInputData,
} from './submitToneBoundaries'
import type { ChallengeOutputBoundary } from '../../boundaries/challengeOutputBoundary'
import type { AttemptGateway } from '../../boundaries/dataAccessInterfaces'

export const TONE_MIN_LENGTH = 1
export const TONE_MAX_LENGTH = 200

export class SubmitToneInteractor implements SubmitToneInputBoundary {
  private readonly store: SessionStore
  private readonly gateway: AttemptGateway
  private readonly output: ChallengeOutputBoundary

  constructor(
    store: SessionStore,
    gateway: AttemptGateway,
    output: ChallengeOutputBoundary,
  ) {
    this.store = store
    this.gateway = gateway
    this.output = output
  }

  setTone(input: ToneInputData): void {
    const session = this.store.get()
    if (!session) return
    session.changeTone(input.answer.slice(0, TONE_MAX_LENGTH))
    this.present(session)
  }

  async execute(input: SubmitToneInputData): Promise<void> {
    const session = this.store.get()
    if (!session) return
    const state = session.snapshot()
    if (state.tonePending || state.stage !== 'tone') return

    const answer = input.answer.trim()
    if (answer.length < TONE_MIN_LENGTH || answer.length > TONE_MAX_LENGTH) {
      session.recordToneError(
        `Tone must be between ${TONE_MIN_LENGTH} and ${TONE_MAX_LENGTH} characters.`,
      )
      this.present(session)
      return
    }

    session.changeTone(answer)
    session.beginToneSubmission()
    this.present(session)

    try {
      const snapshot = await this.gateway.submitTone(
        state.attemptId,
        session.snapshot().tone,
        input.signal,
      )
      if (input.signal.aborted) return
      session.recordToneSuccess(snapshot)
      this.present(session)
    } catch (error) {
      if (input.signal.aborted) return
      session.recordToneError(
        error instanceof Error
          ? error.message
          : 'Tone scoring failed. Please try again.',
      )
      this.present(session)
    }
  }

  private present(session: ChallengeSession): void {
    this.output.present({ status: 'ready', session: session.snapshot() })
  }
}
