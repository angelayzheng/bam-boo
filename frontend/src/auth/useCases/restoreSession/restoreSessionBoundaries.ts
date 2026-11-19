import type { AuthUser } from '../../../entities/types'

export interface RestoreSessionInputData {
  signal: AbortSignal
}

export type RestoreSessionOutputData =
  | { status: 'ready'; user: AuthUser | null }
  | { status: 'error'; message: string }

export interface RestoreSessionInputBoundary {
  execute(input: RestoreSessionInputData): Promise<void>
}

export interface RestoreSessionOutputBoundary {
  present(output: RestoreSessionOutputData): void
}
