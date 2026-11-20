import type { ReactNode } from 'react'
import type {
  CalendarViewModel,
  HomeChallengeViewModel,
  LeaderboardViewModel,
} from '../viewModels/homeViewModel'
import CalendarGrid from './CalendarGrid'
import DailyChallengeCard from './DailyChallengeCard'
import LeaderboardCard from './LeaderboardCard'
import WeekdayStrip from './WeekdayStrip'

interface HomeDashboardProps {
  notice?: ReactNode
  challenge: HomeChallengeViewModel
  calendar: CalendarViewModel
  leaderboard: LeaderboardViewModel
  onStart: () => void
  onPreviousMonth: () => void
  onNextMonth: () => void
}

export default function HomeDashboard({
  notice,
  challenge,
  calendar,
  leaderboard,
  onStart,
  onPreviousMonth,
  onNextMonth,
}: HomeDashboardProps) {
  return (
    <main className="mx-auto grid max-w-7xl min-w-0 gap-10 px-5 py-8 sm:px-8 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.6fr)]">
      {notice && <div className="min-w-0 lg:col-span-2">{notice}</div>}

      <div className="flex min-w-0 flex-col gap-10">
        <DailyChallengeCard viewModel={challenge} onStart={onStart} />
        <LeaderboardCard viewModel={leaderboard} />
      </div>

      <div className="flex min-w-0 flex-col gap-10">
        <WeekdayStrip />
        <CalendarGrid
          viewModel={calendar}
          todayChallengeName={challenge.name}
          onStart={onStart}
          onPreviousMonth={onPreviousMonth}
          onNextMonth={onNextMonth}
        />
      </div>
    </main>
  )
}
