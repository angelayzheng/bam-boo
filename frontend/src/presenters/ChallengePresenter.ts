import type { Challenge, ConversationNode, ResultData } from '../types'
import type { SessionState } from '../entities/challengeSession'
import { responseOptions } from '../entities/conversationRules.ts'
import { challengeDateLabel } from './challengeDatePresenter.ts'
import type {
  ChallengeOutputBoundary,
  ChallengeOutputData,
} from '../boundaries/challengeOutputBoundary'

export interface ChallengeViewModel {
  status: 'loading' | 'error' | 'ready' | 'complete'
  message: string
  dateLabel: string
  challenge: Challenge | null
  session: SessionState | null
  result: ResultData | null
  options: ConversationNode[]
  conversationFinished: boolean
  stepNumber: number
  progressPercent: number
}

const loadingViewModel = (): ChallengeViewModel => ({
  status: 'loading',
  message: '',
  dateLabel: '',
  challenge: null,
  session: null,
  result: null,
  options: [],
  conversationFinished: false,
  stepNumber: 1,
  progressPercent: 33,
})

export function initialChallengeViewModel(): ChallengeViewModel {
  return loadingViewModel()
}

function stageStep(stage: SessionState['stage']): number {
  return stage === 'tone' ? 1 : stage === 'response' ? 2 : 3
}

export class ChallengePresenter implements ChallengeOutputBoundary {
  private output: ChallengeOutputData | null
  private readonly onChange: (viewModel: ChallengeViewModel) => void

  constructor(
    onChange: (viewModel: ChallengeViewModel) => void,
    initial: ChallengeOutputData | null = null,
  ) {
    this.onChange = onChange
    this.output = initial
  }

  present(output: ChallengeOutputData): void {
    this.output = output
    this.onChange(this.toViewModel())
  }

  toViewModel(): ChallengeViewModel {
    const output = this.output
    if (!output || output.status === 'loading') return loadingViewModel()
    if (output.status === 'error') {
      return { ...loadingViewModel(), status: 'error', message: output.message }
    }
    const step = stageStep(output.session.stage)
    const options = responseOptions(output.session.path)
    return {
      status: output.status,
      message: '',
      dateLabel: challengeDateLabel(output.challenge),
      challenge: output.challenge,
      session: output.session,
      result: output.status === 'complete' ? output.result : null,
      options,
      conversationFinished: options.length === 0,
      stepNumber: step,
      progressPercent: Math.round((step / 3) * 100),
    }
  }
}
