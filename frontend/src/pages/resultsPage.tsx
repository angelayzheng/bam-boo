import Header from '../components/Header'
import AchievementGrid from '../results/components/achievementGrid'
import ResultsActions from '../results/components/resultsActions'
import ResultsSummary from '../results/components/resultsSummary'
import ScoreSaveStatus from '../results/components/scoreSaveStatus'
import type {
  ResultClaimViewModel,
  ResultsViewModel,
} from '../results/viewModels/resultsViewModel'

interface ResultsPageProps {
  viewModel: ResultsViewModel
  claimViewModel: ResultClaimViewModel
  onHome: () => void
  onRetry: () => void
  onRetryClaim: () => void
  onLogin: () => void
  onProfile: () => void
}

export default function ResultsPage({
  viewModel,
  claimViewModel,
  onHome,
  onRetry,
  onRetryClaim,
  onLogin,
  onProfile,
}: ResultsPageProps) {
  if (viewModel.status !== 'ready') {
    return (
      <div className="bg-beige min-h-screen text-black">
        <Header compact onHome={onHome} />
        <main className="mx-auto max-w-3xl px-5 py-6 sm:px-8 sm:py-10">
          <div
            role={viewModel.status === 'unavailable' ? 'alert' : 'status'}
            className="rounded-xl bg-slate-100 px-4 py-3 text-sm text-slate-600"
          >
            <p>{viewModel.message}</p>
            {viewModel.status === 'unavailable' && (
              <ResultsActions onHome={onHome} />
            )}
          </div>
        </main>
      </div>
    )
  }

  return (
    <div className="bg-beige min-h-screen text-black">
      <Header compact onHome={onHome} />
      <main className="mx-auto flex max-w-3xl flex-col items-center px-5 py-12 text-center sm:px-8 sm:py-16">
        <ResultsSummary
          heading={viewModel.heading}
          challengeName={viewModel.challengeName}
          dateLabel={viewModel.dateLabel}
          starCount={viewModel.starCount}
          stars={viewModel.stars}
        />
        <AchievementGrid achievements={viewModel.achievements} />
        <ScoreSaveStatus
          viewModel={claimViewModel}
          onLogin={onLogin}
          onProfile={onProfile}
          onRetry={onRetryClaim}
        />
        <ResultsActions onHome={onHome} onRetry={onRetry} />
      </main>
    </div>
  )
}
