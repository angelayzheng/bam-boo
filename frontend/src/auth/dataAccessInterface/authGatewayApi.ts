import type { AuthUser } from '../../entities/types'
import type {
  AuthCredentials,
  AuthenticationGateway,
  LogoutGateway,
  SessionGateway,
  SignupGroup,
  SignupGroupGateway,
} from '../boundaries/dataAccessInterfaces'
import { basePath, postJson, readResponse } from './httpClient.ts'

async function restoreSession(signal: AbortSignal): Promise<AuthUser | null> {
  const response = await fetch(`${basePath}me/`, {
    credentials: 'same-origin',
    cache: 'no-store',
    signal,
  })
  if (response.status === 401) return null
  return (await readResponse<{ user: AuthUser }>(response)).user
}

async function authenticate(
  action: 'login' | 'signup',
  credentials: AuthCredentials,
  signal?: AbortSignal,
): Promise<AuthUser> {
  return (
    await postJson<{ user: AuthUser }>(
      `${basePath}${action}/`,
      credentials,
      signal,
    )
  ).user
}

async function logout(signal?: AbortSignal): Promise<void> {
  await postJson(`${basePath}logout/`, {}, signal)
}

async function loadGroups(signal: AbortSignal): Promise<SignupGroup[]> {
  const response = await fetch('/api/users/groups/', {
    credentials: 'same-origin',
    cache: 'no-store',
    signal,
  })
  return (await readResponse<{ groups: SignupGroup[] }>(response)).groups
}

export const authApi: SessionGateway &
  AuthenticationGateway &
  LogoutGateway &
  SignupGroupGateway = {
  restoreSession,
  authenticate,
  logout,
  loadGroups,
}
