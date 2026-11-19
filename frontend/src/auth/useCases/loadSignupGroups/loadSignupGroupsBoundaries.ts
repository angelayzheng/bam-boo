import type { SignupGroup } from '../../boundaries/dataAccessInterfaces'

export interface LoadSignupGroupsInputData {
  signal: AbortSignal
}

export type LoadSignupGroupsOutputData =
  | { status: 'ready'; groups: SignupGroup[] }
  | { status: 'error'; message: string }

export interface LoadSignupGroupsInputBoundary {
  execute(input: LoadSignupGroupsInputData): Promise<void>
}

export interface LoadSignupGroupsOutputBoundary {
  present(output: LoadSignupGroupsOutputData): void
}
