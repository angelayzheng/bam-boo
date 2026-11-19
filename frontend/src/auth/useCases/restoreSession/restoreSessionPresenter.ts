import type { SessionViewModel } from '../../viewModels/authViewModel.ts'
import {
  errorSessionViewModel,
  toSessionViewModel,
} from '../../viewModels/authViewModel.ts'
import type {
  RestoreSessionOutputBoundary,
  RestoreSessionOutputData,
} from './restoreSessionBoundaries'

export class RestoreSessionPresenter implements RestoreSessionOutputBoundary {
  private readonly onChange: (viewModel: SessionViewModel) => void

  constructor(onChange: (viewModel: SessionViewModel) => void) {
    this.onChange = onChange
  }

  present(output: RestoreSessionOutputData): void {
    this.onChange(
      output.status === 'error'
        ? errorSessionViewModel(output.message)
        : toSessionViewModel(output.user),
    )
  }
}
