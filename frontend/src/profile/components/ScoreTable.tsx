import type { ProfileScoreViewModel } from '../viewModels/profileViewModel'

interface ScoreTableProps {
  scores: ProfileScoreViewModel[]
}

export default function ScoreTable({ scores }: ScoreTableProps) {
  return (
    <section className="shadow-card mt-6 rounded-2xl bg-white/60 p-6">
      <h2 className="text-2xl font-bold">Best challenge scores</h2>
      {scores.length === 0 ? (
        <p className="mt-3 text-base leading-relaxed text-black/60">
          No saved scores yet. Complete a challenge while logged in to start
          tracking your progress.
        </p>
      ) : (
        <table className="mt-4 w-full text-left text-base">
          <thead>
            <tr className="border-green-light border-b text-black/60">
              <th scope="col" className="py-3 font-medium">
                Challenge
              </th>
              <th scope="col" className="py-3 text-right font-medium">
                Best score
              </th>
            </tr>
          </thead>
          <tbody>
            {scores.map((score) => (
              <tr
                key={score.slug}
                className="border-green-pale border-b last:border-0"
              >
                <th scope="row" className="py-3 font-medium">
                  <span className="block">{score.name}</span>
                  {score.dateLabel && (
                    <span className="block text-sm font-normal text-black/60">
                      {score.dateLabel}
                    </span>
                  )}
                </th>
                <td className="text-green-dark py-3 text-right font-bold">
                  {score.scoreLabel}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  )
}
