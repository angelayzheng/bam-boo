import { useEffect, useMemo, useState } from 'react'
import type { AuthUser } from '../entities/types'
import type { ChallengeSummary } from '../entities/types'
import type { CalendarMonth } from '../entities/calendarEntry'
import { shiftMonth } from '../entities/calendarEntry'
import { computeStreak, localIsoDate } from '../entities/trainingCalendar'
import { leaderboardApi } from '../home/dataAccessInterface/leaderboardGatewayApi'
import { profileApi } from '../home/dataAccessInterface/profileGatewayApi'
import { challengeApi } from '../home/dataAccessInterface/challengeApi'

import type {
  CalendarViewModel,
  HomeChallengeViewModel,
  LeaderboardViewModel,
} from '../home/viewModels/homeViewModel'
import {
  homeReferenceDate,
  initialCalendarViewModel,
  initialLeaderboardViewModel,
  toCalendarViewModelFromEntries,
  toHomeChallengeViewModel,
} from '../home/viewModels/homeViewModel'
import type { BrowseChallengesInputBoundary } from '../home/useCases/browseChallenges/browseChallengesBoundaries'
import { BrowseChallengesInteractor } from '../home/useCases/browseChallenges/browseChallengesInteractor'
import type { BrowseResult } from '../home/useCases/browseChallenges/browseChallengesPresenter'
import { BrowseChallengesPresenter } from '../home/useCases/browseChallenges/browseChallengesPresenter'
import type { LoadLeaderboardInputBoundary } from '../home/useCases/loadLeaderboard/loadLeaderboardBoundaries'
import { LoadLeaderboardInteractor } from '../home/useCases/loadLeaderboard/loadLeaderboardInteractor'
import { LoadLeaderboardPresenter } from '../home/useCases/loadLeaderboard/loadLeaderboardPresenter'
import type { LoadTodayChallengeInputBoundary } from '../home/useCases/loadTodayChallenge/loadTodayChallengeBoundaries'
import { LoadTodayChallengeInteractor } from '../home/useCases/loadTodayChallenge/loadTodayChallengeInteractor'
import { LoadTodayChallengePresenter } from '../home/useCases/loadTodayChallenge/loadTodayChallengePresenter'

interface HomeUseCasePorts {
  today: LoadTodayChallengeInputBoundary
  browse: BrowseChallengesInputBoundary
  leaderboard: LoadLeaderboardInputBoundary
}

interface UseHomeFlowArgs {
  challenge: ChallengeSummary | null
  summaries: ChallengeSummary[]
  user: AuthUser | null
  progressVersion: number
}

export function useHomeFlow({
  challenge,
  summaries,
  user,
  progressVersion,
}: UseHomeFlowArgs): {
  challengeViewModel: HomeChallengeViewModel
  calendarViewModel: CalendarViewModel
  leaderboardViewModel: LeaderboardViewModel
  previousMonth: () => void
  nextMonth: () => void
} {
  const referenceDate = homeReferenceDate(challenge)
  const [challengeViewModel, setChallengeViewModel] = useState(() =>
    toHomeChallengeViewModel(challenge),
  )
  const [month, setMonth] = useState<CalendarMonth>(() => ({
    year: Number(referenceDate.slice(0, 4)),
    month: Number(referenceDate.slice(5, 7)),
  }))
  const [browseResult, setBrowseResult] = useState<BrowseResult | null>(null)
  const [streak, setStreak] = useState(0)
  const [leaderboardViewModel, setLeaderboardViewModel] = useState(
    initialLeaderboardViewModel,
  )

  const calendarViewModel = useMemo(
    () =>
      browseResult === null
        ? initialCalendarViewModel(referenceDate)
        : toCalendarViewModelFromEntries(
            browseResult.month,
            browseResult.entries,
            streak,
            browseResult.error ? 'error' : 'ready',
            browseResult.error,
          ),
    [browseResult, streak, referenceDate],
  )

  const useCases = useMemo<HomeUseCasePorts>(() => {
    const today: LoadTodayChallengeInputBoundary =
      new LoadTodayChallengeInteractor(
        new LoadTodayChallengePresenter(setChallengeViewModel),
      )
    const browse: BrowseChallengesInputBoundary =
      new BrowseChallengesInteractor(
        challengeApi,
        new BrowseChallengesPresenter(setBrowseResult),
      )
    const leaderboard: LoadLeaderboardInputBoundary =
      new LoadLeaderboardInteractor(
        leaderboardApi,
        new LoadLeaderboardPresenter(setLeaderboardViewModel),
      )
    return { today, browse, leaderboard }
  }, [])

  useEffect(() => {
    if (summaries.length === 0) return
    useCases.today.execute({ summaries })
  }, [useCases, summaries])

  useEffect(() => {
    const controller = new AbortController()
    void useCases.browse.execute({ month, signal: controller.signal })
    return () => controller.abort()
  }, [useCases, month, user?.username, progressVersion])

  useEffect(() => {
    const controller = new AbortController()
    if (!user) {
      setStreak(0)
      return () => controller.abort()
    }
    profileApi
      .loadProgress(user.username, controller.signal)
      .then((progress) =>
        setStreak(computeStreak(progress.loginDays, localIsoDate(new Date()))),
      )
      .catch(() => {
        if (!controller.signal.aborted) setStreak(0)
      })
    return () => controller.abort()
  }, [user?.username, progressVersion])

  useEffect(() => {
    const controller = new AbortController()
    void useCases.leaderboard.execute({
      currentUserId: user?.id ?? null,
      signal: controller.signal,
    })
    return () => controller.abort()
  }, [useCases, user?.id, progressVersion])

  return {
    challengeViewModel,
    calendarViewModel,
    leaderboardViewModel,
    previousMonth: () => setMonth((m) => shiftMonth(m, -1)),
    nextMonth: () => setMonth((m) => shiftMonth(m, 1)),
  }
}
