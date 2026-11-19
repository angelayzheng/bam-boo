import type { AuthUser } from '../../../entities/types'
import type { AuthCredentials } from '../../../entities/authCredentials'

export interface AuthenticateUserInputData {
  action: 'login' | 'signup'
  credentials: AuthCredentials
  signal: AbortSignal
}

export type AuthenticateUserOutputData =
  { status: 'ready'; user: AuthUser } | { status: 'error'; message: string }

export interface AuthenticateUserInputBoundary {
  execute(input: AuthenticateUserInputData): Promise<void>
}

export interface AuthenticateUserOutputBoundary {
  present(output: AuthenticateUserOutputData): void
}
