import type { LeaderboardViewModel } from '../../viewModels/homeViewModel.ts'
import {
  errorLeaderboardViewModel,
  toLeaderboardViewModel,
} from '../../viewModels/homeViewModel.ts'
import type {
  LoadLeaderboardOutputBoundary,
  LoadLeaderboardOutputData,
} from './loadLeaderboardBoundaries'

export class LoadLeaderboardPresenter implements LoadLeaderboardOutputBoundary {
  private readonly onChange: (viewModel: LeaderboardViewModel) => void

  constructor(onChange: (viewModel: LeaderboardViewModel) => void) {
    this.onChange = onChange
  }

  present(output: LoadLeaderboardOutputData): void {
    this.onChange(
      output.status === 'error'
        ? errorLeaderboardViewModel(output.message)
        : toLeaderboardViewModel(output.entries, output.currentUserId),
    )
  }
}
