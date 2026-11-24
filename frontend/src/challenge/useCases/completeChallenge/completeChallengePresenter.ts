import type {
  ChallengeOutputBoundary,
  ChallengeOutputData,
} from '../../boundaries/challengeOutputBoundary'
import type { ResultData } from '../../../entities/types'
import type { ChallengeViewModel } from '../../viewModels/challengeViewModel.ts'
import { toChallengeViewModel } from '../../viewModels/challengeViewModel.ts'

export class CompleteChallengePresenter implements ChallengeOutputBoundary {
  private readonly onChange: (viewModel: ChallengeViewModel) => void
  private readonly onComplete: (result: ResultData) => void

  constructor(
    onChange: (viewModel: ChallengeViewModel) => void,
    onComplete: (result: ResultData) => void,
  ) {
    this.onChange = onChange
    this.onComplete = onComplete
  }

  present(output: ChallengeOutputData): void {
    this.onChange(toChallengeViewModel(output))
    if (output.status === 'complete') {
      this.onComplete(output.result)
    }
  }
}
