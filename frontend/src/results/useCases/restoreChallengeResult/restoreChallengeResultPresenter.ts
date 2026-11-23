import type { ResultData } from '../../../entities/types.ts'
import type { ResultsViewModel } from '../../viewModels/resultsViewModel.ts'
import {
  toResultsViewModel,
  unavailableResultsViewModel,
} from '../../viewModels/resultsViewModel.ts'
import type {
  RestoreChallengeResultOutputBoundary,
  RestoreChallengeResultOutputData,
} from './restoreChallengeResultBoundaries.ts'

export class RestoreChallengeResultPresenter implements RestoreChallengeResultOutputBoundary {
  private readonly onChange: (viewModel: ResultsViewModel) => void
  private readonly onResult: (result: ResultData | null) => void

  constructor(
    onChange: (viewModel: ResultsViewModel) => void,
    onResult: (result: ResultData | null) => void,
  ) {
    this.onChange = onChange
    this.onResult = onResult
  }

  present(output: RestoreChallengeResultOutputData): void {
    if (output.status === 'ready') {
      this.onChange(toResultsViewModel(output.result))
      this.onResult(output.result)
      return
    }
    this.onChange(unavailableResultsViewModel(output.message))
    this.onResult(null)
  }
}
