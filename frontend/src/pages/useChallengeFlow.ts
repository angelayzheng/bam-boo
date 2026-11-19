import { useEffect, useMemo, useState } from 'react'
import type { Challenge, ResultData } from '../entities/types'
import {
  browserClock,
  browserIds,
} from '../challenge/dataAccessInterface/browserServices'
import { challengeApi } from '../challenge/dataAccessInterface/challengeGatewayApi'
import { toneApi } from '../challenge/dataAccessInterface/toneGatewayApi'
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

export interface ChallengeCompletion {
  result: ResultData
  challenge: Challenge
}

export interface ChallengeController {
  setTone: (answer: string) => void
  submitTone: (answer: string, signal: AbortSignal) => Promise<void>
  selectResponse: (responseKey: string) => void
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
  completion: ChallengeCompletion | null
  controller: ChallengeController
  retry: () => void
} {
  const [viewModel, setViewModel] = useState<ChallengeViewModel>(
    initialChallengeViewModel,
  )
  const [completion, setCompletion] = useState<ChallengeCompletion | null>(null)
  const [attempt, setAttempt] = useState(0)

  const flow = useMemo<ChallengeUseCasePorts>(() => {
    const store = createSessionStore()
    const start: StartChallengeInputBoundary = new StartChallengeInteractor(
      challengeApi,
      new StartChallengePresenter(setViewModel),
      browserClock,
      store,
    )
    const submitTone: SubmitToneInputBoundary = new SubmitToneInteractor(
      store,
      toneApi,
      new SubmitTonePresenter(setViewModel),
      browserClock,
    )
    const advance: AdvanceConversationInputBoundary =
      new AdvanceConversationInteractor(
        store,
        new AdvanceConversationPresenter(setViewModel),
      )
    const complete: CompleteChallengeInputBoundary =
      new CompleteChallengeInteractor(
        store,
        new CompleteChallengePresenter(setViewModel, (result, challenge) => {
          setCompletion({ result, challenge })
        }),
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
      selectResponse: (responseKey) =>
        flow.advance.selectResponse({ responseKey }),
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
    completion,
    controller,
    retry: () => {
      setCompletion(null)
      setAttempt((value) => value + 1)
    },
  }
}
