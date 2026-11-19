import { FlameIcon } from '../../components/icons'
import type { CalendarViewModel } from '../viewModels/homeViewModel'
import Stars from './Stars'

interface CalendarGridProps {
  viewModel: CalendarViewModel
  todayChallengeName: string | null
  onStart: () => void
}

export default function CalendarGrid({
  viewModel,
  todayChallengeName,
  onStart,
}: CalendarGridProps) {
  return (
    <section className="min-w-0">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="flex items-center gap-3 text-3xl font-bold">
          <span aria-hidden="true">‹</span>
          {viewModel.monthLabel}
        </h2>
        <p className="text-orange flex items-center gap-1 text-lg font-bold">
          {viewModel.streak}-day streak
          <FlameIcon className="size-5" />
        </p>
      </div>

      {viewModel.status === 'error' && (
        <p
          role="status"
          className="mb-3 rounded-xl bg-slate-100 px-4 py-3 text-sm text-slate-600"
        >
          {viewModel.message}
        </p>
      )}

      <div className="shadow-card overflow-hidden rounded-2xl">
        <div className="bg-green-dark grid grid-cols-7 py-4 text-center text-sm font-semibold text-white uppercase sm:text-lg">
          {viewModel.weekdays.map((day) => (
            <div key={day}>{day}</div>
          ))}
        </div>
        <div className="bg-green-light/60 grid grid-cols-7 gap-px">
          {viewModel.days.map((day) => {
            const canStart = day.isToday && todayChallengeName !== null
            const label = canStart
              ? `Start ${todayChallengeName}`
              : day.inMonth
                ? `${viewModel.monthLabel} ${day.day}`
                : undefined

            return (
              <button
                key={day.key}
                type="button"
                disabled={!canStart}
                onClick={canStart ? onStart : undefined}
                className={`bg-beige flex min-h-16 min-w-0 flex-col items-start gap-1 overflow-hidden p-1.5 text-left sm:min-h-24 sm:p-3 ${day.isToday ? 'bg-orange-light/30 hover:bg-orange-light/50 cursor-pointer' : 'cursor-default'}`}
                aria-label={label}
              >
                {day.inMonth && (
                  <>
                    <span
                      className={`text-sm font-semibold sm:text-xl ${day.isToday ? 'text-orange' : day.isWeekend ? 'text-black/40' : ''}`}
                    >
                      {day.day}
                    </span>
                    {day.missed ? (
                      <span
                        className="text-orange text-sm sm:text-lg"
                        role="img"
                        aria-label="Missed"
                      >
                        ☹
                      </span>
                    ) : (
                      day.score !== null && <Stars value={day.score} />
                    )}
                  </>
                )}
              </button>
            )
          })}
        </div>
      </div>
    </section>
  )
}
