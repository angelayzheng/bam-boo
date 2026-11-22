import { useEffect, useMemo, useState } from 'react'
import type { ResultData } from '../entities/types'
import { attemptApi } from '../challenge/dataAccessInterface/attemptGatewayApi'
import { attemptStorage } from '../challenge/dataAccessInterface/attemptStorage'
import { createSessionStore } from '../challenge/useCases/sessionStore'
import { initialChallengeViewModel } from '../challenge/viewModels/challengeViewModel'
import type { ChallengeViewModel } from '../challenge/viewModels/challengeViewModel'
import type { StartChallengeInputBoundary } from '../challenge/useCases/startChallenge/startChallengeBoundaries'
import { StartChallengeInteractor } from '../challenge/useCases/startChallenge/startChallengeInteractor'
import { StartChallengePresenter } from '../challenge/useCases/startChallenge/startChallengePresenter'
import type { SubmitToneInputBoundary } from '../challenge/useCases/submitTone/submitToneBoundaries'
import { SubmitToneInteractor } from '../challenge/useCases/submitTone/submitToneInteractor'
import { SubmitTonePresenter } from '../challenge/useCases/submitTone/submitTonePresenter'
import type { AdvanceConversationInputBoundary } from '../challenge/useCases/advanceConversation/advanceConversationBoundaries'
import { AdvanceConversationInteractor } from '../challenge/useCases/advanceConversation/advanceConversationInteractor'
import { AdvanceConversationPresenter } from '../challenge/useCases/advanceConversation/advanceConversationPresenter'
import type { CompleteChallengeInputBoundary } from '../challenge/useCases/completeChallenge/completeChallengeBoundaries'
import { CompleteChallengeInteractor } from '../challenge/useCases/completeChallenge/completeChallengeInteractor'
import { CompleteChallengePresenter } from '../challenge/useCases/completeChallenge/completeChallengePresenter'

export interface ChallengeController {
  setTone: (answer: string) => void
  submitTone: (answer: string, signal: AbortSignal) => Promise<void>
  selectChoice: (choiceId: string) => void
  sendChoice: (signal: AbortSignal) => Promise<void>
  continueToAction: (signal: AbortSignal) => Promise<void>
  audioEnded: (transcriptUrl: string) => void
  setAction: (action: string) => void
  finish: (signal: AbortSignal) => Promise<void>
}

interface ChallengeUseCasePorts {
  start: StartChallengeInputBoundary
  submitTone: SubmitToneInputBoundary
  advance: AdvanceConversationInputBoundary
  complete: CompleteChallengeInputBoundary
}

export function useChallengeFlow(slug: string): {
  viewModel: ChallengeViewModel
  completion: ResultData | null
  controller: ChallengeController
  retry: () => void
} {
  const [viewModel, setViewModel] = useState<ChallengeViewModel>(
    initialChallengeViewModel,
  )
  const [completion, setCompletion] = useState<ResultData | null>(null)
  const [attempt, setAttempt] = useState(0)

  const flow = useMemo<ChallengeUseCasePorts>(() => {
    const store = createSessionStore()
    const start: StartChallengeInputBoundary = new StartChallengeInteractor(
      attemptApi,
      attemptStorage,
      new StartChallengePresenter(setViewModel),
      store,
    )
    const submitTone: SubmitToneInputBoundary = new SubmitToneInteractor(
      store,
      attemptApi,
      new SubmitTonePresenter(setViewModel),
    )
    const advance: AdvanceConversationInputBoundary =
      new AdvanceConversationInteractor(
        store,
        attemptApi,
        new AdvanceConversationPresenter(setViewModel),
      )
    const complete: CompleteChallengeInputBoundary =
      new CompleteChallengeInteractor(
        store,
        attemptApi,
        new CompleteChallengePresenter(setViewModel, (result) => {
          setCompletion(result)
        }),
        attemptStorage,
      )
    return { start, submitTone, advance, complete }
  }, [])

  useEffect(() => {
    const controller = new AbortController()
    void flow.start.execute({ slug, signal: controller.signal })
    return () => controller.abort()
  }, [flow, slug, attempt])

  const controller = useMemo<ChallengeController>(
    () => ({
      setTone: (answer) => flow.submitTone.setTone({ answer }),
      submitTone: (answer, signal) =>
        flow.submitTone.execute({ answer, signal }),
      selectChoice: (choiceId) => flow.advance.selectChoice({ choiceId }),
      sendChoice: (signal) => flow.advance.sendChoice({ signal }),
      continueToAction: (signal) => flow.advance.continueToAction({ signal }),
      audioEnded: (transcriptUrl) => flow.advance.audioEnded({ transcriptUrl }),
      setAction: (action) => flow.complete.setAction({ action }),
      finish: (signal) => flow.complete.execute({ signal }),
    }),
    [flow],
  )

  return {
    viewModel,
    completion,
    controller,
    retry: () => {
      setCompletion(null)
      setAttempt((value) => value + 1)
    },
  }
}
