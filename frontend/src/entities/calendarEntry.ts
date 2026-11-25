// Entity: one day of the calendar as decided by the backend.
import type { ChallengeSummary } from './types'

export type CalendarDayStatus =
  'completed' | 'missed' | 'available' | 'upcoming' | 'none'

export interface CalendarEntry {
  date: string // ISO date, e.g. "2026-10-15"
  status: CalendarDayStatus
  stars: number | null
  challenge: ChallengeSummary | null
}

export interface CalendarMonth {
  year: number
  month: number // 1 to 12
}

export function shiftMonth(
  { year, month }: CalendarMonth,
  delta: number,
): CalendarMonth {
  const d = new Date(Date.UTC(year, month - 1 + delta, 1))
  return { year: d.getUTCFullYear(), month: d.getUTCMonth() + 1 }
}

export function monthOfDate(isoDate: string): CalendarMonth {
  return {
    year: Number(isoDate.slice(0, 4)),
    month: Number(isoDate.slice(5, 7)),
  }
}

// The user's choice wins; otherwise follow the reference date, which changes
// when the challenge finishes loading.
export function resolveCalendarMonth(
  referenceDate: string,
  chosen: CalendarMonth | null,
): CalendarMonth {
  return chosen ?? monthOfDate(referenceDate)
}

// Must match CALENDAR_TIME_ZONE in the backend (challenges/domain/calendarClock.py).
export const CALENDAR_TIME_ZONE = 'America/Toronto'

export function calendarToday(now: Date = new Date()): string {
  return new Intl.DateTimeFormat('en-CA', {
    timeZone: CALENDAR_TIME_ZONE,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).format(now) // en-CA formats as YYYY-MM-DD
}
