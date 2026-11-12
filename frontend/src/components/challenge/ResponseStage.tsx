import type { ConversationNode } from '../../types'
import { card, primaryButton } from './styles'

interface ResponseStageProps {
  tone: string
  toneTime: number
  conversationFinished: boolean
  options: ConversationNode[]
  selectedResponse: ConversationNode | null
  onSelect: (response: ConversationNode) => void
  onSend: () => void
  onContinue: () => void
}

export default function ResponseStage({
  tone,
  toneTime,
  conversationFinished,
  options,
  selectedResponse,
  onSelect,
  onSend,
  onContinue,
}: ResponseStageProps) {
  return (
    <div className="animate-fade-in">
      <div className="bg-green-pale/50 mb-5 rounded-2xl px-4 py-3 text-base">
        <span className="font-bold">Tone captured:</span> {tone} · {toneTime}{' '}
        seconds
      </div>
      <section className={card}>
        <p className="text-green-dark text-sm font-bold tracking-[0.15em] uppercase">
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
                key={response.transcript_url}
                className={`flex cursor-pointer items-start gap-4 rounded-2xl border-2 p-4 transition ${selectedResponse === response ? 'border-green-dark bg-green-pale/50' : 'border-green-light hover:bg-green-pale/30 bg-white'}`}
              >
                <input
                  type="radio"
                  name="response"
                  value={response.transcript_url}
                  checked={selectedResponse === response}
                  onChange={() => onSelect(response)}
                  className="accent-green-dark mt-1 size-5 shrink-0"
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
            onClick={conversationFinished ? onContinue : onSend}
            className={primaryButton}
          >
            {conversationFinished ? 'Continue to next action' : 'Send response'}
          </button>
        </div>
      </section>
    </div>
  )
}
