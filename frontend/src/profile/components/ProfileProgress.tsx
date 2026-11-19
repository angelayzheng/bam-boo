import type { ProfileViewModel } from '../viewModels/profileViewModel'
import ProfileStats from './ProfileStats'
import ScoreTable from './ScoreTable'

interface ProfileProgressProps {
  viewModel: ProfileViewModel
  onRetry: () => void
}

export default function ProfileProgress({
  viewModel,
  onRetry,
}: ProfileProgressProps) {
  if (viewModel.status === 'error') {
    return (
      <div className="shadow-card mt-6 rounded-2xl bg-white/60 p-5">
        <p role="alert" className="text-base text-red-800">
          {viewModel.message}
        </p>
        <button
          type="button"
          onClick={onRetry}
          className="text-green-dark mt-3 font-semibold underline underline-offset-4 transition hover:text-black"
        >
          Try again
        </button>
      </div>
    )
  }

  if (viewModel.status === 'loading') {
    return (
      <p role="status" className="mt-6 text-black/60">
        Loading your progress…
      </p>
    )
  }

  return (
    <>
      <ProfileStats
        totalScore={viewModel.totalScore ?? 0}
        completedChallenges={viewModel.completedChallenges ?? 0}
      />
      <ScoreTable scores={viewModel.scores} />
    </>
  )
}
