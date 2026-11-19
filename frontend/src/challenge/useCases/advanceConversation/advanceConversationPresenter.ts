import type {
  ChallengeOutputBoundary,
  ChallengeOutputData,
} from '../../boundaries/challengeOutputBoundary'
import type { ChallengeViewModel } from '../../viewModels/challengeViewModel.ts'
import { toChallengeViewModel } from '../../viewModels/challengeViewModel.ts'

export class AdvanceConversationPresenter implements ChallengeOutputBoundary {
  private readonly onChange: (viewModel: ChallengeViewModel) => void

  constructor(onChange: (viewModel: ChallengeViewModel) => void) {
    this.onChange = onChange
  }

  present(output: ChallengeOutputData): void {
    this.onChange(toChallengeViewModel(output))
  }
}
