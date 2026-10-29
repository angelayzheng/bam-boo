import { useEffect, useRef, useState } from 'react'
import AudioPlayer from '../components/AudioPlayer'
import Header from '../components/Header'
import { ArrowLeftIcon, CheckIcon } from '../components/icons'
import { challengeDateLabel } from '../challenges'
import { matchesAnswer, respond, responseOptions } from '../conversation'
import type { Challenge, ConversationNode, ResultData } from '../types'

type Stage = 'tone' | 'response' | 'action'

interface ChallengePageProps {
  challenge: Challenge
  onExit: () => void
  onComplete: (result: ResultData) => void
}

export default function ChallengePage({
  challenge,
  onExit,
  onComplete,
}: ChallengePageProps) {
  const [stage, setStage] = useState<Stage>('tone')
  const [tone, setTone] = useState('')
  const [toneTime, setToneTime] = useState(0)
  const [toneCorrect, setToneCorrect] = useState(false)
  const [selectedResponse, setSelectedResponse] =
    useState<ConversationNode | null>(null)
  const [path, setPath] = useState<ConversationNode[]>([
    challenge.conversation_tree,
  ])
  const [activeAudio, setActiveAudio] = useState('')
  const options = responseOptions(path)
  const conversationFinished = options.length === 0
  const [nextAction, setNextAction] = useState('')
  const startedAt = useRef(0)

  useEffect(() => {
    startedAt.current = Date.now()
  }, [])

  const submitTone = () => {
    const elapsed = Math.max(
      1,
      Math.round((Date.now() - startedAt.current) / 1000),
    )
    setToneTime(elapsed)
    setToneCorrect(matchesAnswer(tone, challenge.tone))
    setStage('response')
  }

  const submitAction = () => {
    onComplete({
      challengeId: challenge.id,
      attemptId: crypto.randomUUID(),
      completedAt: new Date().toISOString(),
      toneCorrect,
      toneTime,
      actionCorrect: matchesAnswer(nextAction, challenge.required_action),
    })
  }

  const sendResponse = () => {
    if (!selectedResponse) return
    setPath(respond(path, selectedResponse))
    setActiveAudio(selectedResponse.text_file)
    setSelectedResponse(null)
  }

  const stepNumber = stage === 'tone' ? 1 : stage === 'response' ? 2 : 3

  return (
    <div className="min-h-screen bg-[#f7f8f5] text-slate-900">
      <Header compact />
      <main className="mx-auto max-w-3xl px-5 py-6 sm:px-8 sm:py-10">
        <div className="mb-7 flex items-center justify-between">
          <button
            type="button"
            onClick={onExit}
            className="flex items-center gap-1.5 text-sm font-semibold text-slate-500 transition hover:text-slate-900"
          >
            <ArrowLeftIcon /> Exit challenge
          </button>
          <span className="text-right text-xs font-bold tracking-[0.12em] text-[#19856a] uppercase">
            {challengeDateLabel(challenge)}
          </span>
        </div>

        <div className="mb-8">
          <div className="mb-2 flex justify-between text-xs font-semibold text-slate-500">
            <span>Step {stepNumber} of 3</span>
            <span>{Math.round((stepNumber / 3) * 100)}%</span>
          </div>
          <div className="h-1.5 overflow-hidden rounded-full bg-slate-200">
            <div
              className="h-full rounded-full bg-[#29b88e] transition-all duration-500"
              style={{ width: `${(stepNumber / 3) * 100}%` }}
            />
          </div>
        </div>

        <div className="mb-6">
          <p className="text-xs font-bold tracking-[0.14em] text-[#cf6029] uppercase">
            {challenge.category}
          </p>
          <h1 className="mt-2 text-3xl font-bold tracking-[-0.025em] text-[#17243d] sm:text-4xl">
            {challenge.name}
          </h1>
        </div>

        {stage === 'tone' && (
          <div className="animate-[fade-in_.35s_ease-out]">
            <AudioPlayer
              node={challenge.conversation_tree}
              label="Opening statement"
              autoPlay
            />
            <section className="mt-6 rounded-3xl border border-slate-200 bg-white p-6 sm:p-8">
              <p className="text-xs font-bold tracking-[0.15em] text-[#19856a] uppercase">
                Listen for what is underneath
              </p>
              <h2 className="mt-2 text-2xl font-bold tracking-tight text-[#17243d]">
                What is the customer’s emotional tone?
              </h2>
              <p className="mt-2 text-sm leading-6 text-slate-500">
                Use one or two words. Your first instinct is usually best.
              </p>
              <form
                className="mt-6"
                onSubmit={(event) => {
                  event.preventDefault()
                  if (tone.trim()) submitTone()
                }}
              >
                <label htmlFor="tone" className="sr-only">
                  Customer tone
                </label>
                <input
                  id="tone"
                  value={tone}
                  onChange={(event) =>
                    setTone(
                      event.target.value.split(/\s+/).slice(0, 2).join(' '),
                    )
                  }
                  placeholder="e.g. concerned"
                  autoComplete="off"
                  autoFocus
                  className="w-full rounded-2xl border-2 border-slate-200 bg-[#fbfcfa] px-4 py-4 text-lg font-medium text-slate-900 transition outline-none placeholder:text-slate-300 focus:border-[#29b88e] focus:ring-4 focus:ring-[#29b88e]/10"
                />
                <div className="mt-4 flex items-center justify-between gap-4">
                  <p className="text-xs text-slate-400">1–2 words only</p>
                  <button
                    type="submit"
                    disabled={!tone.trim()}
                    className="rounded-xl bg-[#17243d] px-5 py-3 text-sm font-bold text-white transition hover:bg-[#223253] disabled:cursor-not-allowed disabled:opacity-35"
                  >
                    Lock in answer
                  </button>
                </div>
              </form>
            </section>
          </div>
        )}

        {stage !== 'tone' && (
          <section className="mb-6" aria-label="Conversation history">
            <h2 className="mb-4 text-xl font-bold text-[#17243d]">
              Your conversation
            </h2>
            <ol
              className="grid gap-4"
              aria-live="polite"
              aria-relevant="additions"
            >
              {path.map((node, index) => (
                <li
                  key={node.text_file}
                  className={
                    node.type === 'response' ? 'ml-6 sm:ml-12' : 'mr-6 sm:mr-12'
                  }
                >
                  <AudioPlayer
                    node={node}
                    label={
                      node.type === 'question'
                        ? 'Customer'
                        : 'You · Support agent'
                    }
                    autoPlay={activeAudio === node.text_file}
                    onEnded={() =>
                      setActiveAudio(path[index + 1]?.text_file ?? '')
                    }
                  />
                </li>
              ))}
            </ol>
          </section>
        )}

        {stage === 'response' && (
          <div className="animate-[fade-in_.35s_ease-out]">
            <div className="mb-5 rounded-2xl border border-[#bdebdc] bg-[#eefbf6] px-4 py-3 text-sm text-[#176d59]">
              <span className="font-bold">Tone captured:</span> {tone} ·{' '}
              {toneTime} seconds
            </div>
            <section className="rounded-3xl border border-slate-200 bg-white p-6 sm:p-8">
              <p className="text-xs font-bold tracking-[0.15em] text-[#19856a] uppercase">
                Listen and respond
              </p>
              <h2 className="mt-2 text-2xl font-bold tracking-tight text-[#17243d]">
                {conversationFinished
                  ? 'Conversation complete'
                  : 'What would you say next?'}
              </h2>
              <p className="mt-2 text-sm leading-6 text-slate-500">
                {conversationFinished
                  ? 'Review the customer’s final reply, then decide your next action.'
                  : 'Choose your reply. The customer will respond based on the path you take.'}
              </p>
              {!conversationFinished && (
                <fieldset className="mt-6 grid gap-3">
                  <legend className="sr-only">Your next response</legend>
                  {options.map((response) => (
                    <label
                      key={response.text_file}
                      className={`flex cursor-pointer items-start gap-4 rounded-2xl border-2 p-4 transition ${selectedResponse === response ? 'border-[#29b88e] bg-[#eefbf6]' : 'border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50'}`}
                    >
                      <input
                        type="radio"
                        name="response"
                        value={response.text_file}
                        checked={selectedResponse === response}
                        onChange={() => setSelectedResponse(response)}
                        className="mt-1 size-5 shrink-0 accent-[#19856a]"
                      />
                      <span className="text-sm leading-6 font-medium text-slate-700">
                        {response.text}
                      </span>
                    </label>
                  ))}
                </fieldset>
              )}
              <div className="mt-6 flex justify-end">
                <button
                  type="button"
                  disabled={!conversationFinished && selectedResponse === null}
                  onClick={
                    conversationFinished
                      ? () => {
                          setActiveAudio('')
                          setStage('action')
                        }
                      : sendResponse
                  }
                  className="rounded-xl bg-[#17243d] px-5 py-3 text-sm font-bold text-white transition hover:bg-[#223253] disabled:cursor-not-allowed disabled:opacity-35"
                >
                  {conversationFinished
                    ? 'Continue to next action'
                    : 'Send response'}
                </button>
              </div>
            </section>
          </div>
        )}

        {stage === 'action' && (
          <section className="animate-[fade-in_.35s_ease-out] rounded-3xl border border-slate-200 bg-white p-6 shadow-[0_16px_45px_-28px_rgba(15,23,42,0.35)] sm:p-8">
            <div className="grid size-12 place-items-center rounded-2xl bg-[#fff0e8] text-[#cf6029]">
              <CheckIcon className="size-6" />
            </div>
            <p className="mt-6 text-xs font-bold tracking-[0.15em] text-[#19856a] uppercase">
              Close the loop
            </p>
            <h2 className="mt-2 text-2xl font-bold tracking-tight text-[#17243d]">
              What action will you take next?
            </h2>
            <p className="mt-2 max-w-xl text-sm leading-6 text-slate-500">
              Write the next operational step you would take after this
              conversation.
            </p>
            <form
              className="mt-6"
              onSubmit={(event) => {
                event.preventDefault()
                if (nextAction.trim()) submitAction()
              }}
            >
              <label htmlFor="next-action" className="sr-only">
                Next action
              </label>
              <textarea
                id="next-action"
                rows={4}
                value={nextAction}
                onChange={(event) => setNextAction(event.target.value)}
                placeholder="Describe the action you would take…"
                autoFocus
                className="w-full resize-none rounded-2xl border-2 border-slate-200 bg-[#fbfcfa] px-4 py-4 text-base leading-6 text-slate-900 transition outline-none placeholder:text-slate-300 focus:border-[#29b88e] focus:ring-4 focus:ring-[#29b88e]/10"
              />
              <div className="mt-4 flex justify-end">
                <button
                  type="submit"
                  disabled={!nextAction.trim()}
                  className="rounded-xl bg-[#17243d] px-6 py-3 text-sm font-bold text-white transition hover:bg-[#223253] disabled:cursor-not-allowed disabled:opacity-35"
                >
                  Finish challenge
                </button>
              </div>
            </form>
          </section>
        )}
      </main>
    </div>
  )
}
