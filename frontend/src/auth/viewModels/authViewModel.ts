import type { AuthUser } from '../../entities/types'
import type { SignupGroup } from '../boundaries/dataAccessInterfaces'

export interface SessionViewModel {
  status: 'ready' | 'error'
  user: AuthUser | null
  message: string
}

export interface AuthFormViewModel {
  status: 'ready' | 'error'
  user: AuthUser | null
  message: string
}

export interface SignupGroupsViewModel {
  status: 'ready' | 'error'
  groups: SignupGroup[]
  message: string
}

export interface LogoutViewModel {
  status: 'idle' | 'pending' | 'ready' | 'error'
  message: string
}

export function initialLogoutViewModel(): LogoutViewModel {
  return { status: 'idle', message: '' }
}

export function toSessionViewModel(user: AuthUser | null): SessionViewModel {
  return { status: 'ready', user, message: '' }
}

export function errorSessionViewModel(message: string): SessionViewModel {
  return { status: 'error', user: null, message }
}

export function toAuthFormViewModel(user: AuthUser): AuthFormViewModel {
  return { status: 'ready', user, message: '' }
}

export function errorAuthFormViewModel(message: string): AuthFormViewModel {
  return { status: 'error', user: null, message }
}

export function toSignupGroupsViewModel(
  groups: SignupGroup[],
): SignupGroupsViewModel {
  return { status: 'ready', groups, message: '' }
}

export function errorSignupGroupsViewModel(
  message: string,
): SignupGroupsViewModel {
  return { status: 'error', groups: [], message }
}

export function toLogoutViewModel(): LogoutViewModel {
  return { status: 'ready', message: '' }
}

export function errorLogoutViewModel(message: string): LogoutViewModel {
  return { status: 'error', message }
}
