// HTTP adapter: implements HomeChallengeGateway with GET /api/calendar/.

import type {
  CalendarDayStatus,
  CalendarEntry,
  CalendarMonth,
} from '../../entities/calendarEntry'
import type { HomeChallengeGateway } from '../boundaries/dataAccessInterfaces'

const STATUSES: CalendarDayStatus[] = [
  'completed',
  'missed',
  'available',
  'upcoming',
  'none',
]

function isStatus(value: unknown): value is CalendarDayStatus {
  return STATUSES.includes(value as CalendarDayStatus)
}

function isNullable<T>(
  value: unknown,
  check: (v: unknown) => v is T,
): value is T | null {
  return value === null || check(value)
}

const isString = (v: unknown): v is string => typeof v === 'string'
const isNumber = (v: unknown): v is number =>
  typeof v === 'number' && Number.isFinite(v)

interface CalendarDayJson {
  date: string
  status: CalendarDayStatus
  stars: number | null
  slug: string | null
  name: string | null
  difficulty: number | null
  category: string | null
}

function isCalendarDayJson(value: unknown): value is CalendarDayJson {
  if (typeof value !== 'object' || value === null) return false
  const day = value as Record<string, unknown>
  return (
    isString(day.date) &&
    isStatus(day.status) &&
    isNullable(day.stars, isNumber) &&
    isNullable(day.slug, isString) &&
    isNullable(day.name, isString) &&
    isNullable(day.difficulty, isNumber) &&
    isNullable(day.category, isString)
  )
}

function toEntry(day: CalendarDayJson): CalendarEntry {
  const hasChallenge =
    day.slug !== null &&
    day.name !== null &&
    day.difficulty !== null &&
    day.category !== null
  return {
    date: day.date,
    status: day.status,
    stars: day.stars,
    challenge: hasChallenge
      ? {
          slug: day.slug as string,
          name: day.name as string,
          difficulty: day.difficulty as number,
          category: day.category as string,
          challenge_date: day.date,
        }
      : null,
  }
}

async function browseChallenges(
  { year, month }: CalendarMonth,
  signal: AbortSignal,
): Promise<CalendarEntry[]> {
  const response = await fetch(`/api/calendar/?year=${year}&month=${month}`, {
    credentials: 'same-origin',
    cache: 'no-store',
    signal,
  })
  if (
    !response.ok ||
    !response.headers.get('content-type')?.includes('application/json')
  ) {
    throw new Error(
      'Could not load the calendar. Check that the Django backend is running.',
    )
  }
  const data: unknown = await response.json()
  const days = (data as { days?: unknown } | null)?.days
  if (!Array.isArray(days) || !days.every(isCalendarDayJson)) {
    throw new Error('The calendar returned an unexpected format.')
  }
  return days.map(toEntry)
}

export const challengeApi: HomeChallengeGateway = {
  browseChallenges,
}
