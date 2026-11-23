import { useEffect, useMemo, useState } from 'react'
import type { AuthUser } from '../entities/types'
import type { ChallengeSummary } from '../entities/types'
import { resolveCalendarMonth, shiftMonth } from '../entities/calendarEntry'
import type { CalendarMonth } from '../entities/calendarEntry'
import { computeStreak, localIsoDate } from '../entities/loginStreak'
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
  const [chosenMonth, setChosenMonth] = useState<CalendarMonth | null>(null)
  const month = useMemo(
    () => resolveCalendarMonth(referenceDate, chosenMonth),
    [referenceDate, chosenMonth],
  )
  const [browseResult, setBrowseResult] = useState<BrowseResult | null>(null)
  const username = user?.username ?? null
  const [streakState, setStreakState] = useState<{
    username: string | null
    value: number
  }>({ username: null, value: 0 })

  // Derived: a streak loaded for someone else, or before logging out, never shows.
  const streak = streakState.username === username ? streakState.value : 0
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
    if (!username) return
    const controller = new AbortController()
    profileApi
      .loadProgress(username, controller.signal)
      .then((progress) => {
        if (controller.signal.aborted) return
        setStreakState({
          username,
          value: computeStreak(progress.loginDays, localIsoDate(new Date())),
        })
      })
      .catch(() => {
        if (!controller.signal.aborted) setStreakState({ username, value: 0 })
      })
    return () => controller.abort()
  }, [username, progressVersion])

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
    previousMonth: () => setChosenMonth(shiftMonth(month, -1)),
    nextMonth: () => setChosenMonth(shiftMonth(month, 1)),
  }
}
