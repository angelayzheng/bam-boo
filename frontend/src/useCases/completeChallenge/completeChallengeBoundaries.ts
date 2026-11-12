export interface ActionInputData {
  action: string
}

export interface CompleteChallengeInputBoundary {
  setAction(input: ActionInputData): void
  execute(): void
}
