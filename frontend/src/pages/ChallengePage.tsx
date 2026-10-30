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

const primaryButton =
  'rounded-xl bg-orange px-5 py-3 text-base font-bold text-white transition hover:brightness-95 focus-visible:outline-3 focus-visible:outline-offset-2 focus-visible:outline-green-dark disabled:cursor-not-allowed disabled:opacity-40'

const card = 'rounded-2xl bg-white/60 p-6 shadow-card sm:p-8'

const textField =
  'w-full rounded-2xl border-2 border-green-light bg-white px-4 py-4 text-black transition outline-none placeholder:text-black/30 focus:border-green-dark focus:ring-4 focus:ring-green-dark/10'

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
    <div className="min-h-screen bg-beige text-black">
      <Header compact />
      <main className="mx-auto max-w-3xl px-5 py-6 sm:px-8 sm:py-10">
        <div className="mb-7 flex items-center justify-between">
          <button
            type="button"
            onClick={onExit}
            className="flex items-center gap-1.5 text-base font-semibold text-black/60 transition hover:text-black"
          >
            <ArrowLeftIcon /> Exit challenge
          </button>
          <span className="text-right text-sm font-bold tracking-[0.12em] text-green-dark uppercase">
            {challengeDateLabel(challenge)}
          </span>
        </div>

        <div className="mb-8">
          <div className="mb-2 flex justify-between text-sm font-semibold text-black/60">
            <span>Step {stepNumber} of 3</span>
            <span>{Math.round((stepNumber / 3) * 100)}%</span>
          </div>
          <div className="h-2 overflow-hidden rounded-full bg-green-pale">
            <div
              className="h-full rounded-full bg-green-dark transition-all duration-500"
              style={{ width: `${(stepNumber / 3) * 100}%` }}
            />
          </div>
        </div>

        <div className="mb-6">
          <p className="text-sm font-bold tracking-[0.14em] text-orange uppercase">
            {challenge.category}
          </p>
          <h1 className="mt-2 text-3xl font-extrabold text-orange sm:text-4xl">
            {challenge.name}
          </h1>
        </div>

        {stage === 'tone' && (
          <div className="animate-fade-in">
            <AudioPlayer
              node={challenge.conversation_tree}
              label="Opening statement"
              autoPlay
            />
            <section className={`mt-6 ${card}`}>
              <p className="text-sm font-bold tracking-[0.15em] text-green-dark uppercase">
                Listen for what is underneath
              </p>
              <h2 className="mt-2 text-2xl font-bold">
                What is the customer’s emotional tone?
              </h2>
              <p className="mt-2 text-base leading-6 text-black/60">
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
                  className={`${textField} text-lg font-medium`}
                />
                <div className="mt-4 flex items-center justify-between gap-4">
                  <p className="text-sm text-black/50">1–2 words only</p>
                  <button
                    type="submit"
                    disabled={!tone.trim()}
                    className={primaryButton}
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
            <h2 className="mb-4 text-2xl font-bold">Your conversation</h2>
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
          <div className="animate-fade-in">
            <div className="mb-5 rounded-2xl bg-green-pale/50 px-4 py-3 text-base">
              <span className="font-bold">Tone captured:</span> {tone} ·{' '}
              {toneTime} seconds
            </div>
            <section className={card}>
              <p className="text-sm font-bold tracking-[0.15em] text-green-dark uppercase">
                Listen and respond
              </p>
              <h2 className="mt-2 text-2xl font-bold">
                {conversationFinished
                  ? 'Conversation complete'
                  : 'What would you say next?'}
              </h2>
              <p className="mt-2 text-base leading-6 text-black/60">
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
                      className={`flex cursor-pointer items-start gap-4 rounded-2xl border-2 p-4 transition ${selectedResponse === response ? 'border-green-dark bg-green-pale/50' : 'border-green-light bg-white hover:bg-green-pale/30'}`}
                    >
                      <input
                        type="radio"
                        name="response"
                        value={response.text_file}
                        checked={selectedResponse === response}
                        onChange={() => setSelectedResponse(response)}
                        className="mt-1 size-5 shrink-0 accent-green-dark"
                      />
                      <span className="text-base leading-6 font-medium">
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
                  className={primaryButton}
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
          <section className={`animate-fade-in ${card}`}>
            <div className="grid size-12 place-items-center rounded-2xl bg-orange-light/40 text-orange">
              <CheckIcon className="size-6" />
            </div>
            <p className="mt-6 text-sm font-bold tracking-[0.15em] text-green-dark uppercase">
              Close the loop
            </p>
            <h2 className="mt-2 text-2xl font-bold">
              What action will you take next?
            </h2>
            <p className="mt-2 max-w-xl text-base leading-6 text-black/60">
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
                className={`${textField} resize-none text-base leading-6`}
              />
              <div className="mt-4 flex justify-end">
                <button
                  type="submit"
                  disabled={!nextAction.trim()}
                  className={primaryButton}
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