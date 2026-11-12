import { useEffect, useMemo, useState } from 'react'
import type { ConversationNode } from '../types'
import {
  browserClock,
  browserIds,
} from '../dataAccessInterface/browserServices'
import { challengeApi } from '../dataAccessInterface/challengeGatewayApi'
import { toneApi } from '../dataAccessInterface/toneGatewayApi'
import {
  ChallengePresenter,
  initialChallengeViewModel,
} from '../presenters/ChallengePresenter'
import type { ChallengeViewModel } from '../presenters/ChallengePresenter'
import { createSessionStore } from '../useCases/sessionStore'
import type { StartChallengeInputBoundary } from '../useCases/startChallenge/startChallengeBoundaries'
import { StartChallengeInteractor } from '../useCases/startChallenge/startChallengeInteractor'
import type { SubmitToneInputBoundary } from '../useCases/submitTone/submitToneBoundaries'
import { SubmitToneInteractor } from '../useCases/submitTone/submitToneInteractor'
import type { AdvanceConversationInputBoundary } from '../useCases/advanceConversation/advanceConversationBoundaries'
import { AdvanceConversationInteractor } from '../useCases/advanceConversation/advanceConversationInteractor'
import type { CompleteChallengeInputBoundary } from '../useCases/completeChallenge/completeChallengeBoundaries'
import { CompleteChallengeInteractor } from '../useCases/completeChallenge/completeChallengeInteractor'

export interface ChallengeController {
  setTone: (answer: string) => void
  submitTone: (answer: string, signal: AbortSignal) => Promise<void>
  selectResponse: (response: ConversationNode) => void
  sendResponse: () => void
  continueToAction: () => void
  audioEnded: (transcriptUrl: string) => void
  setAction: (action: string) => void
  finish: () => void
}

interface ChallengeUseCasePorts {
  start: StartChallengeInputBoundary
  submitTone: SubmitToneInputBoundary
  advance: AdvanceConversationInputBoundary
  complete: CompleteChallengeInputBoundary
}

export function useChallengeFlow(date: string): {
  viewModel: ChallengeViewModel
  controller: ChallengeController
  retry: () => void
} {
  const [viewModel, setViewModel] = useState<ChallengeViewModel>(
    initialChallengeViewModel,
  )
  const [attempt, setAttempt] = useState(0)

  const flow = useMemo<ChallengeUseCasePorts>(() => {
    const store = createSessionStore()
    const presenter = new ChallengePresenter(setViewModel)
    const start: StartChallengeInputBoundary = new StartChallengeInteractor(
      challengeApi,
      presenter,
      browserClock,
      store,
    )
    const submitTone: SubmitToneInputBoundary = new SubmitToneInteractor(
      store,
      toneApi,
      presenter,
      browserClock,
    )
    const advance: AdvanceConversationInputBoundary =
      new AdvanceConversationInteractor(store, presenter)
    const complete: CompleteChallengeInputBoundary =
      new CompleteChallengeInteractor(
        store,
        presenter,
        browserIds,
        browserClock,
      )
    return { start, submitTone, advance, complete }
  }, [])

  useEffect(() => {
    const controller = new AbortController()
    void flow.start.execute({ date, signal: controller.signal })
    return () => controller.abort()
  }, [flow, date, attempt])

  const controller = useMemo<ChallengeController>(
    () => ({
      setTone: (answer) => flow.submitTone.setTone({ answer }),
      submitTone: (answer, signal) =>
        flow.submitTone.execute({ answer, signal }),
      selectResponse: (response) => flow.advance.selectResponse({ response }),
      sendResponse: () => flow.advance.sendResponse(),
      continueToAction: () => flow.advance.continueToAction(),
      audioEnded: (transcriptUrl) => flow.advance.audioEnded({ transcriptUrl }),
      setAction: (action) => flow.complete.setAction({ action }),
      finish: () => flow.complete.execute(),
    }),
    [flow],
  )

  return {
    viewModel,
    controller,
    retry: () => setAttempt((value) => value + 1),
  }
}
