import type { AttemptSnapshot, ChallengeSummary } from '../../entities/types'

export interface ChallengeGateway {
  loadSummaries(signal: AbortSignal): Promise<ChallengeSummary[]>
}

export interface AttemptGateway {
  start(slug: string, signal: AbortSignal): Promise<AttemptSnapshot>
  load(attemptId: string, signal: AbortSignal): Promise<AttemptSnapshot | null>
  submitTone(
    attemptId: string,
    answer: string,
    signal: AbortSignal,
  ): Promise<AttemptSnapshot>
  chooseResponse(
    attemptId: string,
    choiceId: string,
    signal: AbortSignal,
  ): Promise<AttemptSnapshot>
  continueConversation(
    attemptId: string,
    signal: AbortSignal,
  ): Promise<AttemptSnapshot>
  submitAction(
    attemptId: string,
    answer: string,
    signal: AbortSignal,
  ): Promise<AttemptSnapshot>
}

export interface AttemptStorage {
  load(slug: string): string | null
  save(slug: string, attemptId: string): void
  clear(slug: string): void
}
