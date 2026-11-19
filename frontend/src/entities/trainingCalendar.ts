import type { ChallengeSummary } from './types'

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

export interface TrainingCalendar {
  year: number
  monthIndex: number
  days: CalendarDay[]
  streak: number
}

export interface BuildTrainingCalendarInput {
  summaries: ChallengeSummary[]
  scores: Record<string, number>
  loginDays: string[]
  referenceDate: string
  progressKnown: boolean
}

export function localIsoDate(value: Date): string {
  const year = value.getFullYear()
  const month = String(value.getMonth() + 1).padStart(2, '0')
  const day = String(value.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function parseIsoDate(value: string): Date | null {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value)
  if (!match) return null
  const year = Number(match[1])
  const month = Number(match[2])
  const day = Number(match[3])
  const date = new Date(year, month - 1, day)
  if (
    date.getFullYear() !== year ||
    date.getMonth() !== month - 1 ||
    date.getDate() !== day
  ) {
    return null
  }
  return date
}

function addDays(value: Date, days: number): Date {
  return new Date(value.getFullYear(), value.getMonth(), value.getDate() + days)
}

export function computeStreak(
  loginDays: string[],
  referenceDate: string,
): number {
  const days = new Set(loginDays)
  const reference = parseIsoDate(referenceDate) ?? new Date()
  let cursor = reference
  if (!days.has(localIsoDate(cursor))) {
    cursor = addDays(cursor, -1)
    if (!days.has(localIsoDate(cursor))) return 0
  }
  let streak = 0
  while (days.has(localIsoDate(cursor))) {
    streak += 1
    cursor = addDays(cursor, -1)
  }
  return streak
}

export function buildTrainingCalendar(
  input: BuildTrainingCalendarInput,
): TrainingCalendar {
  const reference = parseIsoDate(input.referenceDate) ?? new Date()
  const year = reference.getFullYear()
  const monthIndex = reference.getMonth()
  const daysInMonth = new Date(year, monthIndex + 1, 0).getDate()
  const startWeekday = new Date(year, monthIndex, 1).getDay()
  const cellCount = Math.ceil((startWeekday + daysInMonth) / 7) * 7
  const summaryByDate = new Map(
    input.summaries.map((summary) => [summary.challenge_date, summary]),
  )
  const referenceIso = localIsoDate(reference)

  const days = Array.from({ length: cellCount }, (_, index) => {
    const dayNumber = index - startWeekday + 1
    const inMonth = dayNumber >= 1 && dayNumber <= daysInMonth
    const date = inMonth
      ? localIsoDate(new Date(year, monthIndex, dayNumber))
      : null
    const summary = date ? summaryByDate.get(date) : undefined
    const score = summary ? (input.scores[summary.slug] ?? null) : null
    return {
      key: date ?? `blank-${index}`,
      day: inMonth ? dayNumber : null,
      date,
      inMonth,
      isToday: date === referenceIso,
      isWeekend: index % 7 === 0 || index % 7 === 6,
      hasChallenge: summary !== undefined,
      score,
      missed:
        summary !== undefined &&
        input.progressKnown &&
        score === null &&
        date !== null &&
        date < referenceIso,
    }
  })

  return {
    year,
    monthIndex,
    days,
    streak: computeStreak(input.loginDays, referenceIso),
  }
}
