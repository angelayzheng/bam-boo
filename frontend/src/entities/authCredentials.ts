export interface AuthCredentials {
  username: string
  password: string
  email?: string
  group_id?: number | null
}

export interface AuthFormValues {
  mode: 'login' | 'signup'
  username: string
  email: string
  password: string
  confirmation: string
  groupId: string
}

export function passwordsMatch(
  password: string,
  confirmation: string,
): boolean {
  return password === confirmation
}

export function buildCredentials(values: AuthFormValues): AuthCredentials {
  const credentials: AuthCredentials = {
    username: values.username.trim(),
    password: values.password,
  }
  if (values.mode === 'signup') {
    credentials.email = values.email.trim()
    if (values.groupId) credentials.group_id = Number(values.groupId)
  }
  return credentials
}
