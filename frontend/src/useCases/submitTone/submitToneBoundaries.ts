export interface ToneInputData {
  answer: string
}

export interface SubmitToneInputData {
  answer: string
  signal: AbortSignal
}

export interface SubmitToneInputBoundary {
  setTone(input: ToneInputData): void
  execute(input: SubmitToneInputData): Promise<void>
}
