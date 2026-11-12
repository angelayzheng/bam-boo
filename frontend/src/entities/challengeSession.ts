import type { Challenge, ConversationNode, ResultData } from '../types'
import { matchesAnswer, respond, responseOptions } from './conversationRules.ts'

export type Stage = 'tone' | 'response' | 'action'

export interface SessionState {
  stage: Stage
  tone: string
  tonePending: boolean
  toneError: string
  toneTime: number
  toneCorrect: boolean
  path: ConversationNode[]
  selectedResponse: ConversationNode | null
  activeAudio: string
  nextAction: string
}

export function normalizeToneInput(value: string): string {
  return value.split(/\s+/).slice(0, 2).join(' ')
}

export class ChallengeSession {
  readonly challenge: Challenge
  readonly startedAt: number
  private state: SessionState

  constructor(challenge: Challenge, startedAt: number) {
    if (challenge.conversation_tree.type !== 'question') {
      throw new Error(
        'This recording has no conversation tree. Run the demo seed command in the setup guide.',
      )
    }
    this.challenge = challenge
    this.startedAt = startedAt
    this.state = {
      stage: 'tone',
      tone: '',
      tonePending: false,
      toneError: '',
      toneTime: 0,
      toneCorrect: false,
      path: [challenge.conversation_tree],
      selectedResponse: null,
      activeAudio: '',
      nextAction: '',
    }
  }

  snapshot(): SessionState {
    return { ...this.state, path: [...this.state.path] }
  }

  changeTone(value: string): void {
    this.state.tone = normalizeToneInput(value)
  }

  beginToneSubmission(): void {
    this.state.tonePending = true
    this.state.toneError = ''
  }

  recordToneResult(correct: boolean, elapsed: number): void {
    this.state.tonePending = false
    this.state.toneCorrect = correct
    this.state.toneTime = elapsed
    this.state.stage = 'response'
  }

  recordToneError(message: string): void {
    this.state.tonePending = false
    this.state.toneError = message
  }

  selectResponse(node: ConversationNode): void {
    this.state.selectedResponse = node
  }

  sendResponse(): void {
    if (!this.state.selectedResponse) return
    this.state.path = respond(this.state.path, this.state.selectedResponse)
    this.state.activeAudio = this.state.selectedResponse.transcript_url
    this.state.selectedResponse = null
  }

  continueToAction(): void {
    if (responseOptions(this.state.path).length > 0) {
      throw new Error(
        'Finish the conversation before continuing to the next action.',
      )
    }
    this.state.activeAudio = ''
    this.state.stage = 'action'
  }

  advanceAudio(transcriptUrl: string): void {
    const index = this.state.path.findIndex(
      (node) => node.transcript_url === transcriptUrl,
    )
    if (index === -1) return
    this.state.activeAudio = this.state.path[index + 1]?.transcript_url ?? ''
  }

  changeAction(value: string): void {
    this.state.nextAction = value
  }

  buildResult(attemptId: string, completedAt: string): ResultData {
    return {
      challengeSlug: this.challenge.slug,
      attemptId,
      completedAt,
      toneCorrect: this.state.toneCorrect,
      toneTime: this.state.toneTime,
      actionCorrect: matchesAnswer(
        this.state.nextAction,
        this.challenge.required_action,
      ),
    }
  }
}
