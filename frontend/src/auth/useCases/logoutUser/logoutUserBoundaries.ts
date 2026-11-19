export interface LogoutUserInputData {
  signal?: AbortSignal
}

export type LogoutUserOutputData =
  { status: 'ready' } | { status: 'error'; message: string }

export interface LogoutUserInputBoundary {
  execute(input: LogoutUserInputData): Promise<void>
}

export interface LogoutUserOutputBoundary {
  present(output: LogoutUserOutputData): void
}
