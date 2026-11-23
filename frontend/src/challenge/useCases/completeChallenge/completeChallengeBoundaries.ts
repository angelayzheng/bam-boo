export interface ActionInputData {
  action: string
}

export interface CompleteChallengeInputData {
  signal: AbortSignal
}

export interface CompleteChallengeInputBoundary {
  setAction(input: ActionInputData): void
  execute(input: CompleteChallengeInputData): Promise<void>
}
