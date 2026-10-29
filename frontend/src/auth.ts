export interface AuthUser {
  id: number
  username: string
  email: string
}

export interface UserProfile {
  user_id: number
  username: string
  avatar: string
  total_score: number
  completed_challenges: number
  scores: Record<string, number>
}

export interface Credentials {
  username: string
  password: string
  email?: string
}

const basePath = '/api/users/auth/'

async function readResponse<T>(response: Response): Promise<T> {
  if (!response.headers.get('content-type')?.includes('application/json')) {
    throw new Error(
      response.status === 403
        ? 'Your security token expired. Please try again.'
        : 'Could not connect to your account. Please try again.',
    )
  }
  const data = await response.json()
  if (!response.ok) {
    const messages = data.errors
      ? Object.values(data.errors).flat().join(' ')
      : data.detail
    throw new Error(messages || 'Your request failed. Please try again.')
  }
  return data as T
}

export async function getCurrentUser(
  signal: AbortSignal,
): Promise<AuthUser | null> {
  const response = await fetch(`${basePath}me/`, {
    credentials: 'same-origin',
    cache: 'no-store',
    signal,
  })
  if (response.status === 401) return null
  return (await readResponse<{ user: AuthUser }>(response)).user
}

async function authPost<T>(
  action: string,
  credentials?: Credentials,
  signal?: AbortSignal,
): Promise<T> {
  // Fetch the current token for every mutation, including after login rotation.
  const tokenResponse = await fetch(`${basePath}csrf/`, {
    credentials: 'same-origin',
    cache: 'no-store',
    signal,
  })
  const { csrfToken } = await readResponse<{ csrfToken: string }>(tokenResponse)
  const response = await fetch(`${basePath}${action}/`, {
    method: 'POST',
    credentials: 'same-origin',
    signal,
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': csrfToken,
    },
    body: JSON.stringify(credentials ?? {}),
  })
  return readResponse<T>(response)
}

export async function signIn(
  action: 'login' | 'signup',
  credentials: Credentials,
  signal?: AbortSignal,
): Promise<AuthUser> {
  return (await authPost<{ user: AuthUser }>(action, credentials, signal)).user
}

export async function signOut(): Promise<void> {
  await authPost('logout')
}

export async function loadProfile(
  userId: number,
  signal: AbortSignal,
): Promise<UserProfile> {
  const response = await fetch(`/api/users/${userId}/profile/`, {
    credentials: 'same-origin',
    cache: 'no-store',
    signal,
  })
  return readResponse<UserProfile>(response)
}
