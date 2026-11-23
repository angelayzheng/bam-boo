export interface SelectChoiceInputData {
  choiceId: string
}

export interface SendChoiceInputData {
  signal: AbortSignal
}

export interface ContinueToActionInputData {
  signal: AbortSignal
}

export interface AudioEndedInputData {
  transcriptUrl: string
}

export interface AdvanceConversationInputBoundary {
  selectChoice(input: SelectChoiceInputData): void
  sendChoice(input: SendChoiceInputData): Promise<void>
  continueToAction(input: ContinueToActionInputData): Promise<void>
  audioEnded(input: AudioEndedInputData): void
}
