import type { AuthUser } from '../../entities/types'
import type { AuthCredentials } from '../../entities/authCredentials'

export type { AuthCredentials }

export interface SignupGroup {
  id: number
  name: string
}

export interface SessionGateway {
  restoreSession(signal: AbortSignal): Promise<AuthUser | null>
}

export interface AuthenticationGateway {
  authenticate(
    action: 'login' | 'signup',
    credentials: AuthCredentials,
    signal?: AbortSignal,
  ): Promise<AuthUser>
}

export interface LogoutGateway {
  logout(signal?: AbortSignal): Promise<void>
}

export interface SignupGroupGateway {
  loadGroups(signal: AbortSignal): Promise<SignupGroup[]>
}
