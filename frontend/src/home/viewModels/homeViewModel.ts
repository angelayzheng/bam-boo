import type { ChallengeSummary } from '../../entities/types'
import type {
  CalendarDay,
  TrainingCalendar,
} from '../../entities/trainingCalendar'
import {
  buildTrainingCalendar,
  localIsoDate,
} from '../../entities/trainingCalendar.ts'
import {
  challengeDate,
  challengeDateLabel,
} from '../../viewModels/challengeDatePresenter.ts'
import type { LeaderboardEntry } from '../boundaries/dataAccessInterfaces'
import type { CalendarEntry, CalendarMonth } from '../../entities/calendarEntry'

export const WEEKDAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']

export interface HomeChallengeViewModel {
  name: string | null
  dateLabel: string
  available: boolean
}

export function toHomeChallengeViewModel(
  challenge: ChallengeSummary | null,
): HomeChallengeViewModel {
  const date = challenge ? challengeDate(challenge) : new Date()
  return {
    name: challenge?.name ?? null,
    dateLabel: challenge
      ? challengeDateLabel(challenge)
      : new Intl.DateTimeFormat('en-CA', {
          month: 'long',
          day: 'numeric',
          year: 'numeric',
        }).format(date),
    available: challenge !== null,
  }
}

export interface CalendarViewModel {
  status: 'ready' | 'error'
  monthLabel: string
  weekdays: string[]
  days: CalendarDay[]
  streak: number
  message: string
}

export function initialCalendarViewModel(
  referenceDate: string,
): CalendarViewModel {
  return toCalendarViewModel(
    buildTrainingCalendar({
      summaries: [],
      scores: {},
      loginDays: [],
      referenceDate,
      progressKnown: false,
    }),
  )
}

export function toCalendarViewModel(
  calendar: TrainingCalendar,
  status: 'ready' | 'error' = 'ready',
  message = '',
): CalendarViewModel {
  const month = new Date(calendar.year, calendar.monthIndex, 1)
  return {
    status,
    monthLabel: new Intl.DateTimeFormat('en-CA', {
      month: 'long',
      year: 'numeric',
    }).format(month),
    weekdays: [...WEEKDAYS],
    days: calendar.days,
    streak: calendar.streak,
    message,
  }
}

export function toCalendarViewModelFromEntries(
  { year, month }: CalendarMonth,
  entries: CalendarEntry[],
  streak: number,
  status: 'ready' | 'error' = 'ready',
  message = '',
): CalendarViewModel {
  const monthIndex = month - 1
  const startWeekday = new Date(year, monthIndex, 1).getDay()
  const cellCount = Math.ceil((startWeekday + entries.length) / 7) * 7
  const todayIso = localIsoDate(new Date())

  const days: CalendarDay[] = Array.from({ length: cellCount }, (_, index) => {
    const entry = entries[index - startWeekday]
    const weekend = index % 7 === 0 || index % 7 === 6
    if (!entry) {
      return {
        key: `blank-${index}`,
        day: null,
        date: null,
        inMonth: false,
        isToday: false,
        isWeekend: weekend,
        hasChallenge: false,
        score: null,
        missed: false,
      }
    }
    return {
      key: entry.date,
      day: Number(entry.date.slice(8, 10)),
      date: entry.date,
      inMonth: true,
      isToday: entry.date === todayIso,
      isWeekend: weekend,
      hasChallenge: entry.challenge !== null,
      score: entry.stars,
      missed: entry.status === 'missed',
    }
  })

  return {
    status,
    monthLabel: new Intl.DateTimeFormat('en-CA', {
      month: 'long',
      year: 'numeric',
    }).format(new Date(year, monthIndex, 1)),
    weekdays: [...WEEKDAYS],
    days,
    streak,
    message,
  }
}

export interface LeaderboardEntryViewModel {
  rank: number
  name: string
  points: number
  isYou: boolean
}

export interface LeaderboardViewModel {
  status: 'loading' | 'ready' | 'error'
  entries: LeaderboardEntryViewModel[]
  message: string
}

export function initialLeaderboardViewModel(): LeaderboardViewModel {
  return { status: 'loading', entries: [], message: '' }
}

export function toLeaderboardViewModel(
  entries: LeaderboardEntry[],
  currentUserId: number | null,
): LeaderboardViewModel {
  return {
    status: 'ready',
    message: '',
    entries: entries.map((entry, index) => ({
      rank: index + 1,
      name: entry.username,
      points: entry.totalScore,
      isYou: entry.userId === currentUserId,
    })),
  }
}

export function errorLeaderboardViewModel(
  message: string,
): LeaderboardViewModel {
  return { status: 'error', entries: [], message }
}

export function homeReferenceDate(challenge: ChallengeSummary | null): string {
  return challenge?.challenge_date ?? localIsoDate(new Date())
}
