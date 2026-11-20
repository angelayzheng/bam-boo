export interface StartChallengeInputData {
  slug: string
  signal: AbortSignal
}

export interface StartChallengeInputBoundary {
  execute(input: StartChallengeInputData): Promise<void>
}
