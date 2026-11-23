import type { AttemptTurn } from '../../entities/types'
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
  toneCorrect: boolean | null
  toneTime: number
  toneSpeedCorrect: boolean | null
  opening: ChallengeAudioTurnViewModel | null
  path: ChallengeAudioTurnViewModel[]
  activeAudio: string
  options: ChallengeResponseOptionViewModel[]
  choicePending: boolean
  choiceError: string
  continuePending: boolean
  continueError: string
  conversationFinished: boolean
  stepNumber: number
  progressPercent: number
  nextAction: string
  actionPending: boolean
  actionError: string
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
  toneCorrect: null,
  toneTime: 0,
  toneSpeedCorrect: null,
  opening: null,
  path: [],
  activeAudio: '',
  options: [],
  choicePending: false,
  choiceError: '',
  continuePending: false,
  continueError: '',
  conversationFinished: false,
  stepNumber: 1,
  progressPercent: 33,
  nextAction: '',
  actionPending: false,
  actionError: '',
})

export function initialChallengeViewModel(): ChallengeViewModel {
  return loadingViewModel()
}

function stageStep(stage: ChallengeStage): number {
  return stage === 'tone' ? 1 : stage === 'response' ? 2 : 3
}

function toAudioTurn(node: AttemptTurn): ChallengeAudioTurnViewModel {
  return {
    key: node.transcriptUrl,
    type: node.type,
    text: node.text,
    transcriptUrl: node.transcriptUrl,
    audioUrl: node.audioUrl,
  }
}

function displayStage(status: string): ChallengeStage {
  return status === 'tone'
    ? 'tone'
    : status === 'conversation'
      ? 'response'
      : 'action'
}

export function toChallengeViewModel(
  output: ChallengeOutputData | null,
): ChallengeViewModel {
  if (!output || output.status === 'loading') return loadingViewModel()
  if (output.status === 'error') {
    return { ...loadingViewModel(), status: 'error', message: output.message }
  }
  const { session } = output
  const stage = displayStage(session.stage)
  const step = stageStep(stage)
  return {
    status: output.status,
    message: '',
    dateLabel: challengeDateLabel(session.challenge),
    name: session.challenge.name,
    category: session.challenge.category,
    stage,
    tone: session.tone,
    tonePending: session.tonePending,
    toneError: session.toneError,
    toneCorrect: session.toneCorrect,
    toneTime: session.toneTime === null ? 0 : Math.round(session.toneTime),
    toneSpeedCorrect: session.toneSpeedCorrect,
    opening: toAudioTurn(session.opening),
    path: session.conversation.map(toAudioTurn),
    activeAudio: session.activeAudio,
    options: session.choices.map((choice) => ({
      key: choice.choiceId,
      text: choice.text,
      selected: choice.choiceId === session.selectedChoiceId,
    })),
    choicePending: session.choicePending,
    choiceError: session.choiceError,
    continuePending: session.continuePending,
    continueError: session.continueError,
    conversationFinished:
      session.stage === 'conversation' && session.choices.length === 0,
    stepNumber: step,
    progressPercent: Math.round((step / 3) * 100),
    nextAction: session.nextAction,
    actionPending: session.actionPending,
    actionError: session.actionError,
  }
}
