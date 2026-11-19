import type { HomeChallengeViewModel } from '../../viewModels/homeViewModel.ts'
import { toHomeChallengeViewModel } from '../../viewModels/homeViewModel.ts'
import type {
  LoadTodayChallengeOutputBoundary,
  LoadTodayChallengeOutputData,
} from './loadTodayChallengeBoundaries'

export class LoadTodayChallengePresenter implements LoadTodayChallengeOutputBoundary {
  private readonly onChange: (viewModel: HomeChallengeViewModel) => void

  constructor(onChange: (viewModel: HomeChallengeViewModel) => void) {
    this.onChange = onChange
  }

  present(output: LoadTodayChallengeOutputData): void {
    this.onChange(toHomeChallengeViewModel(output.challenge))
  }
}
