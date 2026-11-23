import type {
  CalendarEntry,
  CalendarMonth,
} from '../../../entities/calendarEntry'
import type {
  BrowseChallengesOutputBoundary,
  BrowseChallengesOutputData,
} from './browseChallengesBoundaries'

export interface BrowseResult {
  month: CalendarMonth
  entries: CalendarEntry[]
  error: string
}

export class BrowseChallengesPresenter implements BrowseChallengesOutputBoundary {
  private readonly onChange: (result: BrowseResult) => void

  constructor(onChange: (result: BrowseResult) => void) {
    this.onChange = onChange
  }

  present(output: BrowseChallengesOutputData): void {
    this.onChange({
      month: output.month,
      entries: output.entries,
      error: output.status === 'error' ? output.message : '',
    })
  }
}
