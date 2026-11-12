import { useEffect, useRef } from 'react'
import Header from '../components/Header'
import { scrollIntoView } from '../dataAccessInterface/browserServices'
import { useChallengeFlow } from './useChallengeFlow'
import type { Challenge, ResultData } from '../types'
import ChallengeHeader from '../components/challenge/ChallengeHeader'
import {
  ChallengeLoadError,
  ChallengeLoading,
} from '../components/challenge/ChallengeLoading'
import ToneStage from '../components/challenge/ToneStage'
import ConversationHistory from '../components/challenge/ConversationHistory'
import ResponseStage from '../components/challenge/ResponseStage'
import ActionStage from '../components/challenge/ActionStage'

interface ChallengePageProps {
  date: string
  onExit: () => void
  onComplete: (result: ResultData, challenge: Challenge) => void
}

export default function ChallengePage({
  date,
  onExit,
  onComplete,
}: ChallengePageProps) {
  const { viewModel, controller, retry } = useChallengeFlow(date)
  const toneRequest = useRef<AbortController | null>(null)
  const endRef = useRef<HTMLDivElement>(null)
  const lastSeen = useRef({ length: 0, stage: '' })
  const completedRef = useRef(false)

  useEffect(() => {
    return () => toneRequest.current?.abort()
  }, [])

  useEffect(() => {
    const session = viewModel.session
    if (!session) {
      return
    }
    const last = lastSeen.current
    if (last.length === session.path.length && last.stage === session.stage) {
      return
    }
    lastSeen.current = { length: session.path.length, stage: session.stage }
    scrollIntoView(endRef.current)
  }, [viewModel.session])

  useEffect(() => {
    if (!viewModel.result || completedRef.current || !viewModel.challenge) {
      return
    }
    completedRef.current = true
    onComplete(viewModel.result, viewModel.challenge)
  }, [viewModel, onComplete])

  const submitTone = (answer: string) => {
    const toneController = new AbortController()
    toneRequest.current = toneController
    void controller.submitTone(answer, toneController.signal)
  }

  const session = viewModel.session
  const challenge = viewModel.challenge

  return (
    <div className="bg-beige min-h-screen text-black">
      <Header compact onHome={onExit} />
      <main className="mx-auto max-w-3xl px-5 py-6 sm:px-8 sm:py-10">
        {viewModel.status === 'loading' && <ChallengeLoading />}
        {viewModel.status === 'error' && (
          <ChallengeLoadError message={viewModel.message} onRetry={retry} />
        )}

        {challenge && session && (
          <>
            <ChallengeHeader
              dateLabel={viewModel.dateLabel}
              stepNumber={viewModel.stepNumber}
              progressPercent={viewModel.progressPercent}
              onExit={onExit}
            />

            <div className="mb-6">
              <p className="text-orange text-sm font-bold tracking-[0.14em] uppercase">
                {challenge.category}
              </p>
              <h1 className="text-orange mt-2 text-3xl font-extrabold sm:text-4xl">
                {challenge.name}
              </h1>
            </div>

            {session.stage === 'tone' && (
              <ToneStage
                challenge={challenge}
                tone={session.tone}
                tonePending={session.tonePending}
                toneError={session.toneError}
                onToneChange={controller.setTone}
                onSubmit={() => submitTone(session.tone)}
              />
            )}

            {session.stage !== 'tone' && (
              <ConversationHistory
                path={session.path}
                activeAudio={session.activeAudio}
                onAudioEnded={controller.audioEnded}
              />
            )}

            {session.stage === 'response' && (
              <ResponseStage
                tone={session.tone}
                toneTime={session.toneTime}
                conversationFinished={viewModel.conversationFinished}
                options={viewModel.options}
                selectedResponse={session.selectedResponse}
                onSelect={controller.selectResponse}
                onSend={controller.sendResponse}
                onContinue={controller.continueToAction}
              />
            )}

            {session.stage === 'action' && (
              <ActionStage
                nextAction={session.nextAction}
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
