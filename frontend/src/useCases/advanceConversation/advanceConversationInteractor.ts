import type { ChallengeSession } from '../../entities/challengeSession.ts'
import type { SessionStore } from '../sessionStore.ts'
import type {
  AdvanceConversationInputBoundary,
  AudioEndedInputData,
  SelectResponseInputData,
} from './advanceConversationBoundaries'
import type { ChallengeOutputBoundary } from '../../boundaries/challengeOutputBoundary'

export class AdvanceConversationInteractor implements AdvanceConversationInputBoundary {
  private readonly store: SessionStore
  private readonly output: ChallengeOutputBoundary

  constructor(store: SessionStore, output: ChallengeOutputBoundary) {
    this.store = store
    this.output = output
  }

  selectResponse(input: SelectResponseInputData): void {
    const session = this.store.get()
    if (!session) return
    session.selectResponse(input.response)
    this.present(session)
  }

  sendResponse(): void {
    const session = this.store.get()
    if (!session) return
    session.sendResponse()
    this.present(session)
  }

  continueToAction(): void {
    const session = this.store.get()
    if (!session) return
    session.continueToAction()
    this.present(session)
  }

  audioEnded(input: AudioEndedInputData): void {
    const session = this.store.get()
    if (!session) return
    session.advanceAudio(input.transcriptUrl)
    this.present(session)
  }

  private present(session: ChallengeSession): void {
    this.output.present({
      status: 'ready',
      challenge: session.challenge,
      session: session.snapshot(),
    })
  }
}
