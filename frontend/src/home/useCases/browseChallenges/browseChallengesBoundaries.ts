import type {
  CalendarEntry,
  CalendarMonth,
} from '../../../entities/calendarEntry'

export interface BrowseChallengesInputData {
  month: CalendarMonth
  signal: AbortSignal
}

export type BrowseChallengesOutputData =
  | { status: 'ready'; month: CalendarMonth; entries: CalendarEntry[] }
  | {
      status: 'error'
      month: CalendarMonth
      message: string
      entries: CalendarEntry[]
    }

export interface BrowseChallengesInputBoundary {
  execute(input: BrowseChallengesInputData): Promise<void>
}

export interface BrowseChallengesOutputBoundary {
  present(output: BrowseChallengesOutputData): void
}
