import type { HomeChallengeViewModel } from '../viewModels/homeViewModel'

interface DailyChallengeCardProps {
  viewModel: HomeChallengeViewModel
  onStart: () => void
}

export default function DailyChallengeCard({
  viewModel,
  onStart,
}: DailyChallengeCardProps) {
  return (
    <section className="border-orange overflow-hidden rounded-2xl border">
      <div className="p-6">
        <p className="text-lg font-semibold uppercase">{viewModel.dateLabel}</p>
        <h1 className="text-orange mt-2 text-4xl leading-tight font-extrabold">
          {viewModel.name ?? 'Daily recording'}
        </h1>
        {!viewModel.available && (
          <p className="mt-2 text-lg text-black/70">
            Recordings will appear here when available.
          </p>
        )}
      </div>
      {viewModel.available && (
        <button
          type="button"
          onClick={onStart}
          className="from-orange to-olive focus-visible:outline-green-dark w-full bg-linear-to-b px-6 py-4 text-2xl font-bold text-white transition hover:brightness-105 focus-visible:outline-3 focus-visible:outline-offset-2"
        >
          Start Today’s Challenge
        </button>
      )}
    </section>
  )
}
