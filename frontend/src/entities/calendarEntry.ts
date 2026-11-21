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

export function emptyCalendarEntries({
  year,
  month,
}: CalendarMonth): CalendarEntry[] {
  const daysInMonth = new Date(Date.UTC(year, month, 0)).getUTCDate()
  const mm = String(month).padStart(2, '0')
  return Array.from({ length: daysInMonth }, (_, index): CalendarEntry => ({
    date: `${year}-${mm}-${String(index + 1).padStart(2, '0')}`,
    status: 'none',
    stars: null,
    challenge: null,
  }))
}
