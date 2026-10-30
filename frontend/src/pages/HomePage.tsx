import Header from '../components/Header'
import { FlameIcon } from '../components/icons'
import { challengeDate } from '../challenges'
import type { Challenge } from '../types'

// TODO: replace with real data once the backend provides it.
const MOCK_LEADERBOARD = [
  { rank: 1, name: 'Angelina Jiang', points: 1050 },
  { rank: 2, name: 'Eqraa Khan', points: 985 },
  { rank: 3, name: 'Kenny Zheng', points: 860 },
  { rank: 4, name: 'Laavanya Sahay', points: 800 },
  { rank: 5, name: 'You', points: 750, isYou: true },
  { rank: 6, name: 'Paul Gries', points: 725 },
  { rank: 7, name: 'Mike McCarthy', points: 600 },
]

// Stars out of 3 (halves allowed) per day of the month, or 'missed'.
const MOCK_SCORES: Record<number, number | 'missed'> = {
  1: 3,
  2: 2.5,
  5: 2,
  6: 'missed',
  7: 3,
  8: 0,
  9: 1.5,
  12: 3,
  13: 2,
  14: 3,
}

const WEEKDAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']

function Stars({ value }: { value: number }) {
  return (
    <span
      className="text-green-light flex text-lg leading-none"
      role="img"
      aria-label={`${value} out of 3 stars`}
    >
      {[0, 1, 2].map((i) => {
        const fill = Math.min(1, Math.max(0, value - i))
        return (
          <span key={i} className="relative inline-block">
            <span>☆</span>
            <span
              className="absolute inset-0 overflow-hidden"
              style={{ width: `${fill * 100}%` }}
            >
              ★
            </span>
          </span>
        )
      })}
    </span>
  )
}

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
  const rowStyle = isYou
    ? 'bg-orange-light'
    : rank <= 3
      ? 'bg-green-pale'
      : 'bg-green-pale/30'
  const badgeStyle = isYou
    ? 'bg-beige'
    : rank <= 3
      ? 'bg-orange'
      : 'bg-green-light'

  return (
    <li
      className={`flex items-center gap-4 rounded-xl px-3 py-2.5 shadow-sm ${rowStyle}`}
    >
      <span
        className={`grid size-10 shrink-0 place-items-center rounded-full text-lg font-bold ${badgeStyle}`}
      >
        {rank}
      </span>
      <span className="flex-1 text-xl font-bold">{name}</span>
      <span className="text-xl font-semibold">{points}pts</span>
    </li>
  )
}

interface HomePageProps {
  challenge: Challenge
  onStart: () => void
}

export default function HomePage({ challenge, onStart }: HomePageProps) {
  const challengeDay = challengeDate(challenge)
  const startOfMonth = new Date(
    challengeDay.getFullYear(),
    challengeDay.getMonth(),
    1,
  ).getDay()
  const daysInMonth = new Date(
    challengeDay.getFullYear(),
    challengeDay.getMonth() + 1,
    0,
  ).getDate()
  const calendarDays = Array.from(
    { length: Math.ceil((startOfMonth + daysInMonth) / 7) * 7 },
    (_, index) => index - startOfMonth + 1,
  )

  return (
    <div className="bg-beige min-h-screen text-black">
      <Header />
      <main className="mx-auto grid max-w-7xl min-w-0 gap-10 px-5 py-8 sm:px-8 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.6fr)]">
        {/* Left column */}
        <div className="flex min-w-0 flex-col gap-10">
          <section className="border-orange overflow-hidden rounded-2xl border">
            <div className="p-6">
              <p className="text-lg font-semibold uppercase">
                {new Intl.DateTimeFormat('en-CA', {
                  month: 'long',
                  day: 'numeric',
                  year: 'numeric',
                }).format(challengeDay)}
              </p>
              <h1 className="text-orange mt-2 text-4xl leading-tight font-extrabold">
                {challenge.name}
              </h1>
            </div>
            <button
              type="button"
              onClick={onStart}
              className="from-orange to-olive focus-visible:outline-green-dark w-full bg-linear-to-b px-6 py-4 text-2xl font-bold text-white transition hover:brightness-105 focus-visible:outline-3 focus-visible:outline-offset-2"
            >
              Start Today’s Challenge
            </button>
          </section>

          <section>
            <h2 className="mb-4 text-3xl font-bold">Leaderboard</h2>
            <ul className="flex flex-col gap-3">
              {MOCK_LEADERBOARD.map((entry) => (
                <LeaderboardRow key={entry.rank} {...entry} />
              ))}
            </ul>
            <a
              href="/leaderboard"
              className="text-green-dark mt-4 inline-block text-xl font-bold"
            >
              View Full Leaderboard
            </a>
          </section>
        </div>

        {/* Right column */}
        <div className="flex min-w-0 flex-col gap-10">
          <section className="grid grid-cols-5 gap-2 sm:gap-4">
            {WEEKDAYS.map((day) => (
              <div key={day} className="flex flex-col items-center gap-3">
                <span className="text-xl font-extrabold uppercase sm:text-3xl">
                  {day}
                </span>
                <div className="bg-green-pale shadow-card aspect-square w-full rounded-full" />
              </div>
            ))}
          </section>

          <section className="min-w-0">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="flex items-center gap-3 text-3xl font-bold">
                <span aria-hidden="true">‹</span>
                {new Intl.DateTimeFormat('en-CA', {
                  month: 'long',
                  year: 'numeric',
                }).format(challengeDay)}
              </h2>
              <p className="text-orange flex items-center gap-1 text-lg font-bold">
                3-day streak
                <FlameIcon className="size-5" />
              </p>
            </div>

            <div className="shadow-card overflow-hidden rounded-2xl">
              <div className="bg-green-dark grid grid-cols-7 py-4 text-center text-sm font-semibold text-white uppercase sm:text-lg">
                {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(
                  (day) => (
                    <div key={day}>{day}</div>
                  ),
                )}
              </div>
              <div className="bg-green-light/60 grid grid-cols-7 gap-px">
                {calendarDays.map((day, index) => {
                  const isInMonth = day > 0 && day <= daysInMonth
                  const isToday = day === challengeDay.getDate()
                  const isWeekend = index % 7 === 0 || index % 7 === 6
                  const score = isInMonth ? MOCK_SCORES[day] : undefined

                  return (
                    <button
                      key={`${day}-${index}`}
                      type="button"
                      disabled={!isToday}
                      onClick={isToday ? onStart : undefined}
                      className={`bg-beige flex min-h-16 min-w-0 flex-col items-start gap-1 p-2 text-left sm:min-h-24 sm:p-3 ${isToday ? 'bg-orange-light/30 hover:bg-orange-light/50 cursor-pointer' : 'cursor-default'}`}
                      aria-label={
                        isToday
                          ? `Start ${challenge.name}`
                          : isInMonth
                            ? `${challengeDay.toLocaleString('en-CA', { month: 'long' })} ${day}`
                            : undefined
                      }
                    >
                      {isInMonth && (
                        <>
                          <span
                            className={`text-base font-semibold sm:text-xl ${isToday ? 'text-orange' : isWeekend ? 'text-black/40' : ''}`}
                          >
                            {day}
                          </span>
                          {score === 'missed' ? (
                            <span
                              className="text-orange text-lg"
                              role="img"
                              aria-label="Missed"
                            >
                              ☹
                            </span>
                          ) : (
                            score !== undefined && <Stars value={score} />
                          )}
                        </>
                      )}
                    </button>
                  )
                })}
              </div>
            </div>
          </section>
        </div>
      </main>
    </div>
  )
}
