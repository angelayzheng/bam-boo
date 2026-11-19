import type { LogoutViewModel } from '../../viewModels/authViewModel.ts'
import {
  errorLogoutViewModel,
  toLogoutViewModel,
} from '../../viewModels/authViewModel.ts'
import type {
  LogoutUserOutputBoundary,
  LogoutUserOutputData,
} from './logoutUserBoundaries'

export class LogoutUserPresenter implements LogoutUserOutputBoundary {
  private readonly onChange: (viewModel: LogoutViewModel) => void

  constructor(onChange: (viewModel: LogoutViewModel) => void) {
    this.onChange = onChange
  }

  present(output: LogoutUserOutputData): void {
    this.onChange(
      output.status === 'error'
        ? errorLogoutViewModel(output.message)
        : toLogoutViewModel(),
    )
  }
}
