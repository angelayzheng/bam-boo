import type { SignupGroupsViewModel } from '../../viewModels/authViewModel.ts'
import {
  errorSignupGroupsViewModel,
  toSignupGroupsViewModel,
} from '../../viewModels/authViewModel.ts'
import type {
  LoadSignupGroupsOutputBoundary,
  LoadSignupGroupsOutputData,
} from './loadSignupGroupsBoundaries'

export class LoadSignupGroupsPresenter implements LoadSignupGroupsOutputBoundary {
  private readonly onChange: (viewModel: SignupGroupsViewModel) => void

  constructor(onChange: (viewModel: SignupGroupsViewModel) => void) {
    this.onChange = onChange
  }

  present(output: LoadSignupGroupsOutputData): void {
    this.onChange(
      output.status === 'error'
        ? errorSignupGroupsViewModel(output.message)
        : toSignupGroupsViewModel(output.groups),
    )
  }
}
