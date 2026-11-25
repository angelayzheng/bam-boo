interface ResultsActionsProps {
  onHome: () => void
  onRetry?: () => void
}

export default function ResultsActions({
  onHome,
  onRetry,
}: ResultsActionsProps) {
  return (
    <div className="mt-8 flex w-full flex-col gap-3 sm:flex-row sm:justify-center">
      <button
        type="button"
        onClick={onHome}
        className="bg-orange focus-visible:outline-green-dark rounded-xl px-6 py-3.5 text-base font-bold text-white transition hover:brightness-95 focus-visible:outline-3 focus-visible:outline-offset-2 active:scale-[0.98]"
      >
        Back to calendar
      </button>
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="border-green-dark text-green-dark hover:bg-green-pale/50 focus-visible:outline-green-dark rounded-xl border-2 px-6 py-3.5 text-base font-bold transition focus-visible:outline-3 focus-visible:outline-offset-2 active:scale-[0.98]"
        >
          Retry challenge
        </button>
      )}
    </div>
  )
}
