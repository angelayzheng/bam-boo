import type { ResultClaimViewModel } from '../viewModels/resultsViewModel'

interface ScoreSaveStatusProps {
  viewModel: ResultClaimViewModel
  onLogin: () => void
  onProfile: () => void
  onRetry: () => void
}

const statusLink =
  'text-green-dark font-semibold underline underline-offset-4 transition hover:text-black'

export default function ScoreSaveStatus({
  viewModel,
  onLogin,
  onProfile,
  onRetry,
}: ScoreSaveStatusProps) {
  return (
    <div role="status" className="mt-6 w-full text-base text-black/80">
      {viewModel.message}
      {viewModel.showLogin && (
        <>
          {' '}
          <button type="button" onClick={onLogin} className={statusLink}>
            Log in to save your score
          </button>
        </>
      )}
      {viewModel.showProfile && (
        <>
          {' '}
          <button type="button" onClick={onProfile} className={statusLink}>
            View profile
          </button>
        </>
      )}
      {viewModel.canRetry && (
        <>
          {' '}
          <button type="button" onClick={onRetry} className={statusLink}>
            Retry saving
          </button>
        </>
      )}
    </div>
  )
}
