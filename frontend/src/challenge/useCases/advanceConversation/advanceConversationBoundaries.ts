export interface SelectResponseInputData {
  responseKey: string
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
