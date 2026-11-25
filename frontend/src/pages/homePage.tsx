import type { ReactNode } from 'react'
import Header from '../components/header'
import type { AuthUser, ChallengeSummary } from '../entities/types'
import HomeDashboard from '../home/components/homeDashboard'
import { useHomeFlow } from './useHomeFlow'

interface HomePageProps {
  challenge: ChallengeSummary | null
  summaries: ChallengeSummary[]
  progressVersion: number
  onStart: () => void
  onHome?: () => void
  user: AuthUser | null
  accountLoading: boolean
  onAccount: () => void
  notice?: ReactNode
}

export default function HomePage({
  challenge,
  summaries,
  progressVersion,
  onStart,
  onHome,
  user,
  accountLoading,
  onAccount,
  notice,
}: HomePageProps) {
  const {
    challengeViewModel,
    calendarViewModel,
    leaderboardViewModel,
    previousMonth,
    nextMonth,
  } = useHomeFlow({
    challenge,
    summaries,
    user,
    progressVersion,
  })

  return (
    <div className="bg-beige min-h-screen text-black">
      <Header
        user={user}
        accountLoading={accountLoading}
        onAccount={onAccount}
        onHome={onHome}
        onChallenge={challenge ? onStart : undefined}
      />
      <HomeDashboard
        notice={notice}
        challenge={challengeViewModel}
        calendar={calendarViewModel}
        leaderboard={leaderboardViewModel}
        onStart={onStart}
        onPreviousMonth={previousMonth}
        onNextMonth={nextMonth}
      />
    </div>
  )
}
