export function ChallengeLoading() {
  return (
    <div
      role="status"
      className="rounded-xl bg-slate-100 px-4 py-3 text-sm text-slate-600"
    >
      Loading today’s recording…
    </div>
  )
}

interface ChallengeLoadErrorProps {
  message: string
  onRetry: () => void
}

export function ChallengeLoadError({
  message,
  onRetry,
}: ChallengeLoadErrorProps) {
  return (
    <div
      role="alert"
      className="rounded-xl bg-slate-100 px-4 py-3 text-sm text-slate-600"
    >
      <p>{message}</p>
      <button
        type="button"
        onClick={onRetry}
        className="text-green-dark mt-2 font-semibold underline underline-offset-4"
      >
        Retry loading
      </button>
    </div>
  )
}
