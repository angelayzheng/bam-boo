import type { ConversationNode } from '../../entities/types'
import { responseOptions } from '../../entities/conversationRules.ts'
import { challengeDateLabel } from '../../viewModels/challengeDatePresenter.ts'
import type { ChallengeOutputData } from '../boundaries/challengeOutputBoundary'

export type ChallengeStage = 'tone' | 'response' | 'action'

export interface ChallengeAudioTurnViewModel {
  key: string
  type: 'question' | 'response'
  text: string
  transcriptUrl: string
  audioUrl: string
}

export interface ChallengeResponseOptionViewModel {
  key: string
  text: string
  selected: boolean
}

export interface ChallengeViewModel {
  status: 'loading' | 'error' | 'ready' | 'complete'
  message: string
  dateLabel: string
  name: string | null
  category: string | null
  stage: ChallengeStage
  tone: string
  tonePending: boolean
  toneError: string
  toneTime: number
  opening: ChallengeAudioTurnViewModel | null
  path: ChallengeAudioTurnViewModel[]
  activeAudio: string
  options: ChallengeResponseOptionViewModel[]
  conversationFinished: boolean
  stepNumber: number
  progressPercent: number
  nextAction: string
}

const loadingViewModel = (): ChallengeViewModel => ({
  status: 'loading',
  message: '',
  dateLabel: '',
  name: null,
  category: null,
  stage: 'tone',
  tone: '',
  tonePending: false,
  toneError: '',
  toneTime: 0,
  opening: null,
  path: [],
  activeAudio: '',
  options: [],
  conversationFinished: false,
  stepNumber: 1,
  progressPercent: 33,
  nextAction: '',
})

export function initialChallengeViewModel(): ChallengeViewModel {
  return loadingViewModel()
}

function stageStep(stage: ChallengeStage): number {
  return stage === 'tone' ? 1 : stage === 'response' ? 2 : 3
}

function toAudioTurn(node: ConversationNode): ChallengeAudioTurnViewModel {
  return {
    key: node.transcript_url,
    type: node.type,
    text: node.text,
    transcriptUrl: node.transcript_url,
    audioUrl: node.audio_url,
  }
}

export function toChallengeViewModel(
  output: ChallengeOutputData | null,
): ChallengeViewModel {
  if (!output || output.status === 'loading') return loadingViewModel()
  if (output.status === 'error') {
    return { ...loadingViewModel(), status: 'error', message: output.message }
  }
  const selectedKey = output.session.selectedResponse?.transcript_url ?? null
  const options = responseOptions(output.session.path)
  const step = stageStep(output.session.stage)
  return {
    status: output.status,
    message: '',
    dateLabel: challengeDateLabel(output.challenge),
    name: output.challenge.name,
    category: output.challenge.category,
    stage: output.session.stage,
    tone: output.session.tone,
    tonePending: output.session.tonePending,
    toneError: output.session.toneError,
    toneTime: output.session.toneTime,
    opening: toAudioTurn(output.challenge.conversation_tree),
    path: output.session.path.map(toAudioTurn),
    activeAudio: output.session.activeAudio,
    options: options.map((option) => ({
      key: option.transcript_url,
      text: option.text,
      selected: option.transcript_url === selectedKey,
    })),
    conversationFinished: options.length === 0,
    stepNumber: step,
    progressPercent: Math.round((step / 3) * 100),
    nextAction: output.session.nextAction,
  }
}
