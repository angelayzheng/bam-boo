import type { ConversationNode } from '../../types'

export interface SelectResponseInputData {
  response: ConversationNode
}

export interface AudioEndedInputData {
  transcriptUrl: string
}

export interface AdvanceConversationInputBoundary {
  selectResponse(input: SelectResponseInputData): void
  sendResponse(): void
  continueToAction(): void
  audioEnded(input: AudioEndedInputData): void
}
