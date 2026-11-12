import { ArrowLeftIcon } from '../icons'

interface ChallengeHeaderProps {
  dateLabel: string
  stepNumber: number
  progressPercent: number
  onExit: () => void
}

export default function ChallengeHeader({
  dateLabel,
  stepNumber,
  progressPercent,
  onExit,
}: ChallengeHeaderProps) {
  return (
    <>
      <div className="mb-7 flex items-center justify-between">
        <button
          type="button"
          onClick={onExit}
          className="flex items-center gap-1.5 text-base font-semibold text-black/60 transition hover:text-black"
        >
          <ArrowLeftIcon /> Exit challenge
        </button>
        <span className="text-green-dark text-right text-sm font-bold tracking-[0.12em] uppercase">
          {dateLabel}
        </span>
      </div>

      <div className="mb-8">
        <div className="mb-2 flex justify-between text-sm font-semibold text-black/60">
          <span>Step {stepNumber} of 3</span>
          <span>{progressPercent}%</span>
        </div>
        <div className="bg-green-pale h-2 overflow-hidden rounded-full">
          <div
            className="bg-green-dark h-full rounded-full transition-all duration-500"
            style={{ width: `${progressPercent}%` }}
          />
        </div>
      </div>
    </>
  )
}
