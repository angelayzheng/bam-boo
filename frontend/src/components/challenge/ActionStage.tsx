import { CheckIcon } from '../icons'
import { card, primaryButton, textField } from './styles'

interface ActionStageProps {
  nextAction: string
  onActionChange: (action: string) => void
  onFinish: () => void
}

export default function ActionStage({
  nextAction,
  onActionChange,
  onFinish,
}: ActionStageProps) {
  return (
    <section className={`animate-fade-in ${card}`}>
      <div className="bg-orange-light/40 text-orange grid size-12 place-items-center rounded-2xl">
        <CheckIcon className="size-6" />
      </div>
      <p className="text-green-dark mt-6 text-sm font-bold tracking-[0.15em] uppercase">
        Close the loop
      </p>
      <h2 className="mt-2 text-2xl font-bold">
        What action will you take next?
      </h2>
      <p className="mt-2 max-w-xl text-base leading-6 text-black/60">
        Write the next operational step you would take after this conversation.
      </p>
      <form
        className="mt-6"
        onSubmit={(event) => {
          event.preventDefault()
          if (nextAction.trim()) onFinish()
        }}
      >
        <label htmlFor="next-action" className="sr-only">
          Next action
        </label>
        <textarea
          id="next-action"
          rows={4}
          value={nextAction}
          onChange={(event) => onActionChange(event.target.value)}
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
  )
}
