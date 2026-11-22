import type {
  AttemptChoice,
  AttemptSnapshot,
  AttemptStatus,
  AttemptTurn,
  ChallengeSummary,
  ResultData,
} from './types'

export interface SessionState {
  attemptId: string
  stage: AttemptStatus
  challenge: ChallengeSummary
  opening: AttemptTurn
  conversation: AttemptTurn[]
  choices: AttemptChoice[]
  tone: string
  tonePending: boolean
  toneError: string
  toneCorrect: boolean | null
  toneTime: number | null
  toneSpeedCorrect: boolean | null
  toneSimilarity: number | null
  selectedChoiceId: string | null
  choicePending: boolean
  choiceError: string
  continuePending: boolean
  continueError: string
  activeAudio: string
  nextAction: string
  actionPending: boolean
  actionError: string
  actionCorrect: boolean | null
  score: number | null
  requiredAction: string | null
  completedAt: string | null
}

export function normalizeToneInput(value: string): string {
  return value.split(/\s+/).slice(0, 2).join(' ')
}

export class ChallengeSession {
  private state: SessionState

  constructor(snapshot: AttemptSnapshot) {
    this.state = {
      attemptId: snapshot.attemptId,
      stage: snapshot.stage,
      challenge: snapshot.challenge,
      opening: snapshot.opening,
      conversation: [...snapshot.conversation],
      choices: [...snapshot.choices],
      tone: '',
      tonePending: false,
      toneError: '',
      toneCorrect: snapshot.toneCorrect,
      toneTime: snapshot.toneTime,
      toneSpeedCorrect: snapshot.toneSpeedCorrect,
      toneSimilarity: snapshot.toneSimilarity,
      selectedChoiceId: null,
      choicePending: false,
      choiceError: '',
      continuePending: false,
      continueError: '',
      activeAudio: '',
      nextAction: '',
      actionPending: false,
      actionError: '',
      actionCorrect: snapshot.actionCorrect,
      score: snapshot.score,
      requiredAction: snapshot.requiredAction,
      completedAt: snapshot.completedAt,
    }
  }

  snapshot(): SessionState {
    return {
      ...this.state,
      conversation: [...this.state.conversation],
      choices: [...this.state.choices],
    }
  }

  changeTone(value: string): void {
    this.state.tone = normalizeToneInput(value)
  }

  beginToneSubmission(): void {
    this.state.tonePending = true
    this.state.toneError = ''
  }

  recordToneSuccess(snapshot: AttemptSnapshot): void {
    this.applySnapshot(snapshot)
  }

  recordToneError(message: string): void {
    this.state.tonePending = false
    this.state.toneError = message
  }

  selectChoice(choiceId: string): void {
    const choice = this.state.choices.find((item) => item.choiceId === choiceId)
    if (!choice) {
      throw new Error('Choose a response from the current conversation turn.')
    }
    this.state.selectedChoiceId = choiceId
    this.state.choiceError = ''
  }

  beginChoiceSubmission(): void {
    this.state.choicePending = true
    this.state.choiceError = ''
  }

  recordChoiceSuccess(snapshot: AttemptSnapshot): void {
    const previousLength = this.state.conversation.length
    this.applySnapshot(snapshot)
    this.state.selectedChoiceId = null
    const nextResponse = this.state.conversation
      .slice(previousLength)
      .find((turn) => turn.type === 'response')
    this.state.activeAudio = nextResponse?.transcriptUrl ?? ''
  }

  recordChoiceError(message: string): void {
    this.state.choicePending = false
    this.state.choiceError = message
  }

  beginContinue(): void {
    this.state.continuePending = true
    this.state.continueError = ''
  }

  recordContinueSuccess(snapshot: AttemptSnapshot): void {
    this.applySnapshot(snapshot)
    this.state.activeAudio = ''
  }

  recordContinueError(message: string): void {
    this.state.continuePending = false
    this.state.continueError = message
  }

  advanceAudio(transcriptUrl: string): void {
    const index = this.state.conversation.findIndex(
      (turn) => turn.transcriptUrl === transcriptUrl,
    )
    if (index === -1) return
    this.state.activeAudio =
      this.state.conversation[index + 1]?.transcriptUrl ?? ''
  }

  changeAction(value: string): void {
    this.state.nextAction = value
  }

  beginActionSubmission(): void {
    this.state.actionPending = true
    this.state.actionError = ''
  }

  recordActionResult(snapshot: AttemptSnapshot): void {
    this.applySnapshot(snapshot)
    this.state.activeAudio = ''
  }

  recordActionError(message: string): void {
    this.state.actionPending = false
    this.state.actionError = message
  }

  buildResult(): ResultData {
    const {
      attemptId,
      challenge,
      completedAt,
      toneCorrect,
      toneTime,
      toneSpeedCorrect,
      toneSimilarity,
      actionCorrect,
      score,
      requiredAction,
    } = this.state
    if (
      this.state.stage !== 'completed' ||
      completedAt === null ||
      toneCorrect === null ||
      toneTime === null ||
      toneSpeedCorrect === null ||
      actionCorrect === null ||
      score === null ||
      requiredAction === null
    ) {
      throw new Error('The attempt is not complete.')
    }
    return {
      attemptId,
      challenge,
      completedAt,
      toneCorrect,
      toneTime,
      toneSpeedCorrect,
      toneSimilarity,
      actionCorrect,
      score,
      requiredAction,
    }
  }

  private applySnapshot(snapshot: AttemptSnapshot): void {
    const selectedChoiceId = this.state.selectedChoiceId
    this.state = {
      ...this.state,
      attemptId: snapshot.attemptId,
      stage: snapshot.stage,
      challenge: snapshot.challenge,
      opening: snapshot.opening,
      conversation: [...snapshot.conversation],
      choices: [...snapshot.choices],
      toneCorrect: snapshot.toneCorrect,
      toneTime: snapshot.toneTime,
      toneSpeedCorrect: snapshot.toneSpeedCorrect,
      toneSimilarity: snapshot.toneSimilarity,
      selectedChoiceId: snapshot.choices.some(
        (choice) => choice.choiceId === selectedChoiceId,
      )
        ? selectedChoiceId
        : null,
      tonePending: false,
      toneError: '',
      choicePending: false,
      choiceError: '',
      continuePending: false,
      continueError: '',
      actionPending: false,
      actionError: '',
      actionCorrect: snapshot.actionCorrect,
      score: snapshot.score,
      requiredAction: snapshot.requiredAction,
      completedAt: snapshot.completedAt,
    }
  }
}
