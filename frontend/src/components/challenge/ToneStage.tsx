import AudioPlayer from '../AudioPlayer'
import type { Challenge } from '../../types'
import { card, primaryButton, textField } from './styles'

interface ToneStageProps {
  challenge: Challenge
  tone: string
  tonePending: boolean
  toneError: string
  onToneChange: (answer: string) => void
  onSubmit: () => void
}

export default function ToneStage({
  challenge,
  tone,
  tonePending,
  toneError,
  onToneChange,
  onSubmit,
}: ToneStageProps) {
  return (
    <div className="animate-fade-in">
      <AudioPlayer
        node={challenge.conversation_tree}
        label="Opening statement"
        autoPlay
      />
      <section className={`mt-6 ${card}`}>
        <p className="text-green-dark text-sm font-bold tracking-[0.15em] uppercase">
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
            if (tone.trim()) onSubmit()
          }}
        >
          <label htmlFor="tone" className="sr-only">
            Customer tone
          </label>
          <input
            id="tone"
            disabled={tonePending}
            aria-describedby={toneError ? 'tone-error' : undefined}
            value={tone}
            onChange={(event) => onToneChange(event.target.value)}
            placeholder="e.g. concerned"
            autoComplete="off"
            autoFocus
            className={`${textField} text-lg font-medium`}
          />
          <div className="mt-4 flex items-center justify-between gap-4">
            <p className="text-sm text-black/50">1–2 words only</p>
            <button
              type="submit"
              disabled={!tone.trim() || tonePending}
              className={primaryButton}
            >
              {tonePending ? 'Checking tone…' : 'Lock in answer'}
            </button>
          </div>
          {toneError && (
            <p
              id="tone-error"
              role="alert"
              className="mt-3 text-sm text-red-700"
            >
              {toneError}
            </p>
          )}
        </form>
      </section>
    </div>
  )
}
