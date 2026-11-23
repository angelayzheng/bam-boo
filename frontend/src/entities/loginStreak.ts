// Entity: login streak rules. Scoring and calendar statuses come from the backend.
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
