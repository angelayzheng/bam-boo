import { useEffect, useRef } from 'react'
import Header from '../components/header'
import { scrollIntoView } from '../challenge/dataAccessInterface/browserServices'
import { useChallengeFlow } from './useChallengeFlow'
import type { ResultData } from '../entities/types'
import ChallengeHeader from '../challenge/components/challengeHeader'
import {
  ChallengeLoadError,
  ChallengeLoading,
} from '../challenge/components/challengeLoading'
import ToneStage from '../challenge/components/toneStage'
import ConversationHistory from '../challenge/components/conversationHistory'
import ResponseStage from '../challenge/components/responseStage'
import ActionStage from '../challenge/components/actionStage'

interface ChallengePageProps {
  slug: string
  onExit: () => void
  onComplete: (result: ResultData) => void
}

export default function ChallengePage({
  slug,
  onExit,
  onComplete,
}: ChallengePageProps) {
  const { viewModel, completion, controller, retry } = useChallengeFlow(slug)
  const request = useRef<AbortController | null>(null)
  const endRef = useRef<HTMLDivElement>(null)
  const lastSeen = useRef({ length: 0, stage: '' })
  const completedRef = useRef(false)

  useEffect(() => {
    return () => request.current?.abort()
  }, [])

  useEffect(() => {
    const last = lastSeen.current
    if (
      last.length === viewModel.path.length &&
      last.stage === viewModel.stage
    ) {
      return
    }
    lastSeen.current = {
      length: viewModel.path.length,
      stage: viewModel.stage,
    }
    scrollIntoView(endRef.current)
  }, [viewModel.path.length, viewModel.stage])

  useEffect(() => {
    if (!completion || completedRef.current) {
      return
    }
    completedRef.current = true
    onComplete(completion)
  }, [completion, onComplete])

  const run = (action: (signal: AbortSignal) => Promise<void>) => {
    request.current?.abort()
    const requestController = new AbortController()
    request.current = requestController
    void action(requestController.signal)
  }

  const ready = viewModel.name !== null && viewModel.opening !== null

  return (
    <div className="bg-beige min-h-screen text-black">
      <Header compact onHome={onExit} />
      <main className="mx-auto max-w-3xl px-5 py-6 sm:px-8 sm:py-10">
        {viewModel.status === 'loading' && <ChallengeLoading />}
        {viewModel.status === 'error' && (
          <ChallengeLoadError message={viewModel.message} onRetry={retry} />
        )}

        {ready && (
          <>
            <ChallengeHeader
              dateLabel={viewModel.dateLabel}
              stepNumber={viewModel.stepNumber}
              progressPercent={viewModel.progressPercent}
              onExit={onExit}
            />

            <div className="mb-6">
              <p className="text-orange text-sm font-bold tracking-[0.14em] uppercase">
                {viewModel.category}
              </p>
              <h1 className="text-orange mt-2 text-3xl font-extrabold sm:text-4xl">
                {viewModel.name}
              </h1>
            </div>

            {viewModel.stage === 'tone' && viewModel.opening && (
              <ToneStage
                opening={viewModel.opening}
                tone={viewModel.tone}
                tonePending={viewModel.tonePending}
                toneError={viewModel.toneError}
                onToneChange={controller.setTone}
                onSubmit={() =>
                  run((signal) => controller.submitTone(viewModel.tone, signal))
                }
              />
            )}

            {viewModel.stage !== 'tone' && (
              <ConversationHistory
                path={viewModel.path}
                activeAudio={viewModel.activeAudio}
                onAudioEnded={controller.audioEnded}
              />
            )}

            {viewModel.stage === 'response' && (
              <ResponseStage
                tone={viewModel.tone}
                toneTime={viewModel.toneTime}
                conversationFinished={viewModel.conversationFinished}
                options={viewModel.options}
                choicePending={viewModel.choicePending}
                choiceError={viewModel.choiceError}
                continuePending={viewModel.continuePending}
                continueError={viewModel.continueError}
                onSelect={controller.selectChoice}
                onSend={() => run((signal) => controller.sendChoice(signal))}
                onContinue={() =>
                  run((signal) => controller.continueToAction(signal))
                }
              />
            )}

            {viewModel.stage === 'action' && (
              <ActionStage
                nextAction={viewModel.nextAction}
                actionPending={viewModel.actionPending}
                actionError={viewModel.actionError}
                onActionChange={controller.setAction}
                onFinish={() => run((signal) => controller.finish(signal))}
              />
            )}

            <div ref={endRef} aria-hidden="true" className="scroll-mb-6" />
          </>
        )}
      </main>
    </div>
  )
}
