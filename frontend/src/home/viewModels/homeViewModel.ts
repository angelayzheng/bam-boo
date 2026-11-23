import type { ChallengeSummary } from '../../entities/types'
import { calendarToday, monthOfDate } from '../../entities/calendarEntry.ts'
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

export interface CalendarDay {
  key: string
  day: number | null
  date: string | null
  inMonth: boolean
  isToday: boolean
  isWeekend: boolean
  hasChallenge: boolean
  score: number | null
  missed: boolean
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
  return toCalendarViewModelFromEntries(monthOfDate(referenceDate), [], 0)
}

export function toCalendarViewModelFromEntries(
  { year, month }: CalendarMonth,
  entries: CalendarEntry[],
  streak: number,
  status: 'ready' | 'error' = 'ready',
  message = '',
  todayIso: string = calendarToday(),
): CalendarViewModel {
  const monthIndex = month - 1
  const daysInMonth = new Date(year, month, 0).getDate()
  const startWeekday = new Date(year, monthIndex, 1).getDay()
  const cellCount = Math.ceil((startWeekday + daysInMonth) / 7) * 7
  const byDate = new Map(entries.map((entry) => [entry.date, entry]))
  const prefix = `${String(year).padStart(4, '0')}-${String(month).padStart(2, '0')}`

  const days: CalendarDay[] = Array.from({ length: cellCount }, (_, index) => {
    const dayNumber = index - startWeekday + 1
    const inMonth = dayNumber >= 1 && dayNumber <= daysInMonth
    const isWeekend = index % 7 === 0 || index % 7 === 6
    if (!inMonth) {
      return {
        key: `blank-${index}`,
        day: null,
        date: null,
        inMonth: false,
        isToday: false,
        isWeekend,
        hasChallenge: false,
        score: null,
        missed: false,
      }
    }
    const date = `${prefix}-${String(dayNumber).padStart(2, '0')}`
    const entry = byDate.get(date)
    return {
      key: date,
      day: dayNumber,
      date,
      inMonth: true,
      isToday: date === todayIso,
      isWeekend,
      hasChallenge: Boolean(entry?.challenge),
      score: entry?.stars ?? null,
      missed: entry?.status === 'missed',
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
  return challenge?.challenge_date ?? calendarToday()
}
