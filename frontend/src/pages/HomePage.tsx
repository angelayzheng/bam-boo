import Header from '../components/Header'
import { challengeDate } from '../challenges'
import type { Challenge } from '../types'

interface HomePageProps {
  challenge: Challenge
  onStart: () => void
}

export default function HomePage({ challenge, onStart }: HomePageProps) {
  const levelDate = challengeDate(challenge)
  const startOfMonth = new Date(
    levelDate.getFullYear(),
    levelDate.getMonth(),
    1,
  ).getDay()
  const daysInMonth = new Date(
    levelDate.getFullYear(),
    levelDate.getMonth() + 1,
    0,
  ).getDate()
  const calendarDays = Array.from(
    { length: Math.ceil((startOfMonth + daysInMonth) / 7) * 7 },
    (_, index) => index - startOfMonth + 1,
  )

  return (
    <div className="min-h-screen bg-[#f7f8f5] text-slate-900">
      <Header />
      <main className="mx-auto max-w-6xl min-w-0 px-5 py-8 sm:px-8 sm:py-12">
        <div className="mb-10 flex flex-col justify-between gap-6 md:flex-row md:items-end">
          <div>
            <h1 className="max-w-2xl text-4xl leading-[1.08] font-bold tracking-[-0.035em] text-[#17243d] sm:text-5xl">
              bam-<span className="italic">boo</span>!
            </h1>
          </div>
          <div className="flex gap-3">
            <div className="min-w-28 rounded-2xl border border-slate-200 bg-white px-4 py-3 shadow-sm">
              <p className="text-2xl font-bold text-[#17243d]">1</p>
              <p className="text-xs font-medium text-slate-500">
                Recording ready
              </p>
            </div>
            <div className="min-w-28 rounded-2xl border border-slate-200 bg-white px-4 py-3 shadow-sm">
              <p className="text-2xl font-bold text-[#17243d]">
                {challenge.difficulty}/5
              </p>
              <p className="text-xs font-medium text-slate-500">Difficulty</p>
            </div>
          </div>
        </div>

        <section className="w-full min-w-0 overflow-hidden rounded-[28px] border border-slate-200 bg-white shadow-[0_24px_65px_-40px_rgba(15,23,42,0.3)]">
          <div className="flex flex-col justify-between gap-4 border-b border-slate-100 px-5 py-5 sm:flex-row sm:items-center sm:px-7">
            <div>
              <h2 className="text-xl font-bold tracking-tight text-[#17243d]">
                {new Intl.DateTimeFormat('en-CA', {
                  month: 'long',
                  year: 'numeric',
                }).format(levelDate)}
              </h2>
            </div>
            <div className="flex items-center gap-4 text-xs font-medium text-slate-500">
              <span className="flex items-center gap-1.5">
                <span className="size-2 rounded-full bg-[#ff9b66]" /> Available
                recording
              </span>
            </div>
          </div>

          <div className="p-3 sm:p-6">
            <div className="grid min-w-0 grid-cols-7 text-center text-[9px] font-bold tracking-[0.08em] text-slate-400 uppercase sm:text-[11px] sm:tracking-[0.12em]">
              {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map((day) => (
                <div key={day} className="py-3">
                  {day}
                </div>
              ))}
            </div>
            <div className="grid min-w-0 grid-cols-7 overflow-hidden rounded-2xl border border-slate-200 bg-slate-200">
              {calendarDays.map((day, index) => {
                const isInMonth = day > 0 && day <= daysInMonth
                const isToday = day === levelDate.getDate()
                const isWeekend = index % 7 === 0 || index % 7 === 6

                return (
                  <button
                    key={`${day}-${index}`}
                    type="button"
                    disabled={!isToday}
                    onClick={isToday ? onStart : undefined}
                    className={`relative min-h-17 min-w-0 bg-white p-1.5 text-left transition sm:min-h-24 sm:p-3 ${isToday ? 'group cursor-pointer hover:bg-[#fff7f1]' : 'cursor-default'} ${isWeekend ? 'bg-slate-50/90' : ''}`}
                    aria-label={
                      isToday
                        ? `Start ${challenge.name}`
                        : isInMonth
                          ? `${levelDate.toLocaleString('en-CA', { month: 'long' })} ${day}`
                          : undefined
                    }
                  >
                    {isInMonth && (
                      <>
                        <span
                          className={`text-xs font-semibold ${isToday ? 'text-[#cf6029]' : 'text-slate-500'}`}
                        >
                          {day}
                        </span>
                        {isToday && (
                          <span className="absolute inset-x-1 bottom-1.5 truncate rounded-xl bg-[#ff9b66] px-0.5 py-2 text-center text-[9px] font-bold text-white shadow-sm transition group-hover:bg-[#f28a50] sm:inset-x-3 sm:bottom-3 sm:px-2 sm:text-xs">
                            <span className="sm:hidden">Start</span>
                            <span className="hidden sm:inline">
                              Start level
                            </span>
                          </span>
                        )}
                      </>
                    )}
                  </button>
                )
              })}
            </div>
          </div>
        </section>

        <button
          type="button"
          onClick={onStart}
          className="mt-6 flex w-full items-center justify-between rounded-2xl bg-[#17243d] p-5 text-left text-white shadow-lg shadow-slate-900/10 transition hover:-translate-y-0.5 hover:bg-[#223253] focus-visible:outline-3 focus-visible:outline-offset-3 focus-visible:outline-[#66d9b7] sm:p-6"
        >
          <span>
            <span className="text-xs font-bold tracking-[0.14em] text-[#75e2c1] uppercase">
              {challenge.challenge_date} · {challenge.category}
            </span>
            <span className="mt-1 block text-lg font-bold">
              {challenge.name}
            </span>
          </span>
          <span className="rounded-full bg-white/10 px-4 py-2 text-sm font-semibold">
            Begin →
          </span>
        </button>
      </main>
    </div>
  )
}
