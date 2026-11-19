import type { AuthFormViewModel } from '../../viewModels/authViewModel.ts'
import {
  errorAuthFormViewModel,
  toAuthFormViewModel,
} from '../../viewModels/authViewModel.ts'
import type {
  AuthenticateUserOutputBoundary,
  AuthenticateUserOutputData,
} from './authenticateUserBoundaries'

export class AuthenticateUserPresenter implements AuthenticateUserOutputBoundary {
  private readonly onChange: (viewModel: AuthFormViewModel) => void

  constructor(onChange: (viewModel: AuthFormViewModel) => void) {
    this.onChange = onChange
  }

  present(output: AuthenticateUserOutputData): void {
    this.onChange(
      output.status === 'error'
        ? errorAuthFormViewModel(output.message)
        : toAuthFormViewModel(output.user),
    )
  }
}
