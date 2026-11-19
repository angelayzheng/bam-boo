import type { LeaderboardViewModel } from '../viewModels/homeViewModel'

function LeaderboardRow({
  rank,
  name,
  points,
  isYou = false,
}: {
  rank: number
  name: string
  points: number
  isYou?: boolean
}) {
  return (
    <li
      className={`hover:shadow-card flex items-center gap-4 rounded-xl px-3 py-2.5 shadow-sm transition hover:-translate-y-0.5 ${isYou ? 'bg-orange-light' : 'bg-green-pale/60'}`}
    >
      <span
        className={`grid size-10 shrink-0 place-items-center rounded-full text-lg font-bold text-white ${isYou ? 'bg-orange' : 'bg-green-dark'}`}
      >
        {rank}
      </span>
      <span className="flex-1 text-xl font-bold">{name}</span>
      <span className="text-xl font-semibold">{points}pts</span>
    </li>
  )
}

interface LeaderboardCardProps {
  viewModel: LeaderboardViewModel
}

export default function LeaderboardCard({ viewModel }: LeaderboardCardProps) {
  return (
    <section>
      <h2 className="mb-4 text-3xl font-bold">Leaderboard</h2>
      {viewModel.status === 'error' ? (
        <p
          role="status"
          className="rounded-xl bg-slate-100 px-4 py-3 text-sm text-slate-600"
        >
          {viewModel.message}
        </p>
      ) : (
        <ul className="flex flex-col gap-3">
          {viewModel.entries.map((entry) => (
            <LeaderboardRow key={entry.rank} {...entry} />
          ))}
        </ul>
      )}
      <a
        href="/leaderboard"
        className="text-green-dark mt-4 inline-block text-xl font-bold"
      >
        View Full Leaderboard
      </a>
    </section>
  )
}
