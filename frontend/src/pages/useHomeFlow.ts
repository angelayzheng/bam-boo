import { useEffect, useMemo, useState } from 'react'
import type { AuthUser } from '../entities/types'
import type { ChallengeSummary } from '../entities/types'
import { leaderboardApi } from '../home/dataAccessInterface/leaderboardGatewayApi'
import { profileApi } from '../home/dataAccessInterface/profileGatewayApi'
import type {
  CalendarViewModel,
  HomeChallengeViewModel,
  LeaderboardViewModel,
} from '../home/viewModels/homeViewModel'
import {
  homeReferenceDate,
  initialCalendarViewModel,
  initialLeaderboardViewModel,
} from '../home/viewModels/homeViewModel'
import { toHomeChallengeViewModel } from '../home/viewModels/homeViewModel'
import type { LoadCalendarInputBoundary } from '../home/useCases/loadCalendar/loadCalendarBoundaries'
import { LoadCalendarInteractor } from '../home/useCases/loadCalendar/loadCalendarInteractor'
import { LoadCalendarPresenter } from '../home/useCases/loadCalendar/loadCalendarPresenter'
import type { LoadLeaderboardInputBoundary } from '../home/useCases/loadLeaderboard/loadLeaderboardBoundaries'
import { LoadLeaderboardInteractor } from '../home/useCases/loadLeaderboard/loadLeaderboardInteractor'
import { LoadLeaderboardPresenter } from '../home/useCases/loadLeaderboard/loadLeaderboardPresenter'
import type { LoadTodayChallengeInputBoundary } from '../home/useCases/loadTodayChallenge/loadTodayChallengeBoundaries'
import { LoadTodayChallengeInteractor } from '../home/useCases/loadTodayChallenge/loadTodayChallengeInteractor'
import { LoadTodayChallengePresenter } from '../home/useCases/loadTodayChallenge/loadTodayChallengePresenter'

interface HomeUseCasePorts {
  today: LoadTodayChallengeInputBoundary
  calendar: LoadCalendarInputBoundary
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
} {
  const referenceDate = homeReferenceDate(challenge)
  const [challengeViewModel, setChallengeViewModel] = useState(() =>
    toHomeChallengeViewModel(challenge),
  )
  const [calendarViewModel, setCalendarViewModel] = useState(() =>
    initialCalendarViewModel(referenceDate),
  )
  const [leaderboardViewModel, setLeaderboardViewModel] = useState(
    initialLeaderboardViewModel,
  )

  const useCases = useMemo<HomeUseCasePorts>(() => {
    const today: LoadTodayChallengeInputBoundary =
      new LoadTodayChallengeInteractor(
        new LoadTodayChallengePresenter(setChallengeViewModel),
      )
    const calendar: LoadCalendarInputBoundary = new LoadCalendarInteractor(
      profileApi,
      new LoadCalendarPresenter(setCalendarViewModel),
    )
    const leaderboard: LoadLeaderboardInputBoundary =
      new LoadLeaderboardInteractor(
        leaderboardApi,
        new LoadLeaderboardPresenter(setLeaderboardViewModel),
      )
    return { today, calendar, leaderboard }
  }, [])

  useEffect(() => {
    if (summaries.length === 0) return
    useCases.today.execute({ summaries })
  }, [useCases, summaries])

  useEffect(() => {
    const controller = new AbortController()
    void useCases.calendar.execute({
      summaries,
      referenceDate,
      username: user?.username ?? null,
      signal: controller.signal,
    })
    return () => controller.abort()
  }, [useCases, summaries, referenceDate, user?.username, progressVersion])

  useEffect(() => {
    const controller = new AbortController()
    void useCases.leaderboard.execute({
      currentUserId: user?.id ?? null,
      signal: controller.signal,
    })
    return () => controller.abort()
  }, [useCases, user?.id, progressVersion])

  return { challengeViewModel, calendarViewModel, leaderboardViewModel }
}
