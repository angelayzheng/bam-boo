import { CheckIcon } from '../../components/icons'
import type { AchievementViewModel } from '../viewModels/resultsViewModel'

interface AchievementGridProps {
  achievements: AchievementViewModel[]
}

export default function AchievementGrid({
  achievements,
}: AchievementGridProps) {
  return (
    <div className="grid w-full gap-3 text-left sm:grid-cols-3">
      {achievements.map((achievement) => (
        <div
          key={achievement.title}
          className={`shadow-card rounded-2xl p-5 ${achievement.earned ? 'bg-green-pale/50' : 'bg-white/40'}`}
        >
          <div
            className={`mb-4 grid size-8 place-items-center rounded-full ${achievement.earned ? 'bg-green-dark text-white' : 'bg-black/10 text-black/40'}`}
          >
            {achievement.earned ? (
              <CheckIcon className="size-4" />
            ) : (
              <span className="text-sm font-bold">—</span>
            )}
          </div>
          <h2 className="text-lg font-bold">{achievement.title}</h2>
          <p className="mt-1.5 text-sm leading-5 text-black/70">
            {achievement.detail}
          </p>
        </div>
      ))}
    </div>
  )
}
