import type { AuthUser } from '../../../entities/types'
import type { ProfileViewModel } from '../../viewModels/profileViewModel.ts'
import {
  errorProfileViewModel,
  toProfileViewModel,
} from '../../viewModels/profileViewModel.ts'
import type {
  LoadUserProfileOutputBoundary,
  LoadUserProfileOutputData,
} from './loadUserProfileBoundaries'

export class LoadUserProfilePresenter implements LoadUserProfileOutputBoundary {
  private readonly onChange: (viewModel: ProfileViewModel) => void
  private readonly user: AuthUser

  constructor(onChange: (viewModel: ProfileViewModel) => void, user: AuthUser) {
    this.onChange = onChange
    this.user = user
  }

  present(output: LoadUserProfileOutputData): void {
    this.onChange(
      output.status === 'error'
        ? errorProfileViewModel(output.message, this.user)
        : toProfileViewModel(output.profile, output.progress, this.user),
    )
  }
}
