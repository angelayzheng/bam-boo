import type { ResultData } from '../../../entities/types.ts'
import type { ResultClaimViewModel } from '../../viewModels/resultsViewModel.ts'
import { toResultClaimViewModel } from '../../viewModels/resultsViewModel.ts'
import type {
  ClaimChallengeResultOutputBoundary,
  ClaimChallengeResultOutputData,
} from './claimChallengeResultBoundaries.ts'

export class ClaimChallengeResultPresenter implements ClaimChallengeResultOutputBoundary {
  private readonly onChange: (viewModel: ResultClaimViewModel) => void
  private readonly onClaimed: (result: ResultData) => void
  private readonly onUnauthorized: () => void

  constructor(
    onChange: (viewModel: ResultClaimViewModel) => void,
    onClaimed: (result: ResultData) => void,
    onUnauthorized: () => void,
  ) {
    this.onChange = onChange
    this.onClaimed = onClaimed
    this.onUnauthorized = onUnauthorized
  }

  present(output: ClaimChallengeResultOutputData): void {
    this.onChange(toResultClaimViewModel(output))
    if (output.status === 'saved' && output.claimed) {
      this.onClaimed(output.result)
    }
    if (output.status === 'unauthorized') {
      this.onUnauthorized()
    }
  }
}
