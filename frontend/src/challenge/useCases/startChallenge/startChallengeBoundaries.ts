export interface StartChallengeInputData {
  date: string
  signal: AbortSignal
}

export interface StartChallengeInputBoundary {
  execute(input: StartChallengeInputData): Promise<void>
}
