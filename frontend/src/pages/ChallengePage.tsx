import { useEffect, useRef } from 'react'
import Header from '../components/Header'
import { scrollIntoView } from '../challenge/dataAccessInterface/browserServices'
import { useChallengeFlow } from './useChallengeFlow'
import type { Challenge, ResultData } from '../entities/types'
import ChallengeHeader from '../challenge/components/ChallengeHeader'
import {
  ChallengeLoadError,
  ChallengeLoading,
} from '../challenge/components/ChallengeLoading'
import ToneStage from '../challenge/components/ToneStage'
import ConversationHistory from '../challenge/components/ConversationHistory'
import ResponseStage from '../challenge/components/ResponseStage'
import ActionStage from '../challenge/components/ActionStage'

interface ChallengePageProps {
  slug: string
  onExit: () => void
  onComplete: (result: ResultData, challenge: Challenge) => void
}

export default function ChallengePage({
  slug,
  onExit,
  onComplete,
}: ChallengePageProps) {
  const { viewModel, completion, controller, retry } = useChallengeFlow(slug)
  const toneRequest = useRef<AbortController | null>(null)
  const endRef = useRef<HTMLDivElement>(null)
  const lastSeen = useRef({ length: 0, stage: '' })
  const completedRef = useRef(false)

  useEffect(() => {
    return () => toneRequest.current?.abort()
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
    onComplete(completion.result, completion.challenge)
  }, [completion, onComplete])

  const submitTone = (answer: string) => {
    const toneController = new AbortController()
    toneRequest.current = toneController
    void controller.submitTone(answer, toneController.signal)
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
                onSubmit={() => submitTone(viewModel.tone)}
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
                onSelect={controller.selectResponse}
                onSend={controller.sendResponse}
                onContinue={controller.continueToAction}
              />
            )}

            {viewModel.stage === 'action' && (
              <ActionStage
                nextAction={viewModel.nextAction}
                onActionChange={controller.setAction}
                onFinish={controller.finish}
              />
            )}

            <div ref={endRef} aria-hidden="true" className="scroll-mb-6" />
          </>
        )}
      </main>
    </div>
  )
}
