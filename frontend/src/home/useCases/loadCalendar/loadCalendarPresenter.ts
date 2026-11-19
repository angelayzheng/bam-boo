import type { CalendarViewModel } from '../../viewModels/homeViewModel.ts'
import { toCalendarViewModel } from '../../viewModels/homeViewModel.ts'
import type {
  LoadCalendarOutputBoundary,
  LoadCalendarOutputData,
} from './loadCalendarBoundaries'

export class LoadCalendarPresenter implements LoadCalendarOutputBoundary {
  private readonly onChange: (viewModel: CalendarViewModel) => void

  constructor(onChange: (viewModel: CalendarViewModel) => void) {
    this.onChange = onChange
  }

  present(output: LoadCalendarOutputData): void {
    this.onChange(
      output.status === 'error'
        ? toCalendarViewModel(output.calendar, 'error', output.message)
        : toCalendarViewModel(output.calendar),
    )
  }
}
