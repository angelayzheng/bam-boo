import type { TrainingCalendar } from '../../../entities/trainingCalendar'
import type { ChallengeSummary } from '../../../entities/types'

export interface LoadCalendarInputData {
  summaries: ChallengeSummary[]
  referenceDate: string
  username: string | null
  signal: AbortSignal
}

export type LoadCalendarOutputData =
  | { status: 'ready'; calendar: TrainingCalendar }
  | { status: 'error'; message: string; calendar: TrainingCalendar }

export interface LoadCalendarInputBoundary {
  execute(input: LoadCalendarInputData): Promise<void>
}

export interface LoadCalendarOutputBoundary {
  present(output: LoadCalendarOutputData): void
}
