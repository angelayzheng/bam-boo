export const authBasePath = '/api/users/auth/'

const defaultFallbackMessage =
  'Could not connect to your account. Please try again.'

export class ApiError extends Error {
  status: number

  constructor(message: string, status: number) {
    super(message)
    this.status = status
  }
}

export async function readResponse<T>(
  response: Response,
  fallbackMessage = defaultFallbackMessage,
): Promise<T> {
  if (!response.headers.get('content-type')?.includes('application/json')) {
    throw new Error(
      response.status === 403
        ? 'Your security token expired. Please try again.'
        : fallbackMessage,
    )
  }
  const data = await response.json()
  if (!response.ok) {
    const messages = data.errors
      ? Object.values(data.errors).flat().join(' ')
      : data.detail
    throw new ApiError(messages || fallbackMessage, response.status)
  }
  return data as T
}

export async function getJson<T>(
  path: string,
  signal: AbortSignal,
  fallbackMessage = defaultFallbackMessage,
): Promise<T> {
  const response = await fetch(path, {
    credentials: 'same-origin',
    cache: 'no-store',
    signal,
  })
  return readResponse<T>(response, fallbackMessage)
}

export async function postJson<T>(
  path: string,
  payload: object = {},
  signal?: AbortSignal,
  fallbackMessage = defaultFallbackMessage,
): Promise<T> {
  const tokenResponse = await fetch(`${authBasePath}csrf/`, {
    credentials: 'same-origin',
    cache: 'no-store',
    signal,
  })
  const { csrfToken } = await readResponse<{ csrfToken: string }>(
    tokenResponse,
    fallbackMessage,
  )
  const response = await fetch(path, {
    method: 'POST',
    credentials: 'same-origin',
    signal,
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': csrfToken,
    },
    body: JSON.stringify(payload),
  })
  return readResponse<T>(response, fallbackMessage)
}
