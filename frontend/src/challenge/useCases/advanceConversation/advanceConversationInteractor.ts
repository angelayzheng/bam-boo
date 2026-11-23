import type { ChallengeSession } from '../../../entities/challengeSession.ts'
import type { SessionStore } from '../sessionStore.ts'
import type {
  AdvanceConversationInputBoundary,
  AudioEndedInputData,
  ContinueToActionInputData,
  SelectChoiceInputData,
  SendChoiceInputData,
} from './advanceConversationBoundaries'
import type { ChallengeOutputBoundary } from '../../boundaries/challengeOutputBoundary'
import type { AttemptGateway } from '../../boundaries/dataAccessInterfaces'

export class AdvanceConversationInteractor implements AdvanceConversationInputBoundary {
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

  selectChoice(input: SelectChoiceInputData): void {
    const session = this.store.get()
    if (!session) return
    session.selectChoice(input.choiceId)
    this.present(session)
  }

  async sendChoice(input: SendChoiceInputData): Promise<void> {
    const session = this.store.get()
    if (!session) return
    const state = session.snapshot()
    if (
      state.choicePending ||
      state.stage !== 'conversation' ||
      state.selectedChoiceId === null
    ) {
      return
    }

    session.beginChoiceSubmission()
    this.present(session)
    try {
      const snapshot = await this.gateway.chooseResponse(
        state.attemptId,
        state.selectedChoiceId,
        input.signal,
      )
      if (input.signal.aborted) return
      session.recordChoiceSuccess(snapshot)
      this.present(session)
    } catch (error) {
      if (input.signal.aborted) return
      session.recordChoiceError(
        error instanceof Error
          ? error.message
          : 'Could not send your response. Please try again.',
      )
      this.present(session)
    }
  }

  async continueToAction(input: ContinueToActionInputData): Promise<void> {
    const session = this.store.get()
    if (!session) return
    const state = session.snapshot()
    if (
      state.continuePending ||
      state.stage !== 'conversation' ||
      state.choices.length > 0
    ) {
      return
    }

    session.beginContinue()
    this.present(session)
    try {
      const snapshot = await this.gateway.continueConversation(
        state.attemptId,
        input.signal,
      )
      if (input.signal.aborted) return
      session.recordContinueSuccess(snapshot)
      this.present(session)
    } catch (error) {
      if (input.signal.aborted) return
      session.recordContinueError(
        error instanceof Error
          ? error.message
          : 'Could not continue the challenge. Please try again.',
      )
      this.present(session)
    }
  }

  audioEnded(input: AudioEndedInputData): void {
    const session = this.store.get()
    if (!session) return
    session.advanceAudio(input.transcriptUrl)
    this.present(session)
  }

  private present(session: ChallengeSession): void {
    this.output.present({ status: 'ready', session: session.snapshot() })
  }
}
