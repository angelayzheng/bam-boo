import { useEffect, useMemo, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import type { AuthFlow } from '../auth/components/AuthForm'
import type { SignupGroup } from '../auth/boundaries/dataAccessInterfaces'
import { authApi } from '../auth/dataAccessInterface/authGatewayApi'
import { buildCredentials, passwordsMatch } from '../entities/authCredentials'
import type { AuthUser } from '../entities/types'
import { AuthenticateUserInteractor } from '../auth/useCases/authenticateUser/authenticateUserInteractor'
import { AuthenticateUserPresenter } from '../auth/useCases/authenticateUser/authenticateUserPresenter'
import { LoadSignupGroupsInteractor } from '../auth/useCases/loadSignupGroups/loadSignupGroupsInteractor'
import { LoadSignupGroupsPresenter } from '../auth/useCases/loadSignupGroups/loadSignupGroupsPresenter'

type GroupsStatus = 'loading' | 'ready' | 'error'

interface UseAuthFlowArgs {
  mode: 'login' | 'signup'
  sessionLoading: boolean
  onAuthenticated: (user: AuthUser) => void
}

export function useAuthFlow({
  mode,
  sessionLoading,
  onAuthenticated,
}: UseAuthFlowArgs): AuthFlow {
  const isSignup = mode === 'signup'
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [groupId, setGroupId] = useState('')
  const [password, setPassword] = useState('')
  const [confirmation, setConfirmation] = useState('')
  const [error, setError] = useState('')
  const [pending, setPending] = useState(false)
  const [groups, setGroups] = useState<SignupGroup[]>([])
  const [groupsStatus, setGroupsStatus] = useState<GroupsStatus>('loading')
  const [groupsError, setGroupsError] = useState('')
  const [groupsAttempt, setGroupsAttempt] = useState(0)
  const request = useRef<AbortController | null>(null)

  const authenticate = useMemo(
    () =>
      new AuthenticateUserInteractor(
        authApi,
        new AuthenticateUserPresenter((viewModel) => {
          if (viewModel.status === 'ready' && viewModel.user) {
            setPending(false)
            onAuthenticated(viewModel.user)
            return
          }
          if (viewModel.status === 'error') {
            setError(viewModel.message)
            setPending(false)
          }
        }),
      ),
    [onAuthenticated],
  )

  const loadGroups = useMemo(
    () =>
      new LoadSignupGroupsInteractor(
        authApi,
        new LoadSignupGroupsPresenter((viewModel) => {
          if (viewModel.status === 'ready') {
            setGroups(viewModel.groups)
            setGroupsError('')
            setGroupsStatus('ready')
            return
          }
          setGroups([])
          setGroupsError(viewModel.message)
          setGroupsStatus('error')
        }),
      ),
    [],
  )

  useEffect(() => {
    if (!isSignup) return
    const controller = new AbortController()
    void loadGroups.execute({ signal: controller.signal })
    return () => controller.abort()
  }, [isSignup, groupsAttempt, loadGroups])

  useEffect(() => () => request.current?.abort(), [])

  async function submit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault()
    if (pending || sessionLoading) return
    setError('')
    if (isSignup && !passwordsMatch(password, confirmation)) {
      setError('Your passwords do not match.')
      return
    }
    const controller = new AbortController()
    request.current = controller
    setPending(true)
    await authenticate.execute({
      action: mode,
      credentials: buildCredentials({
        mode,
        username,
        email,
        password,
        confirmation,
        groupId,
      }),
      signal: controller.signal,
    })
  }

  return {
    username,
    email,
    groupId,
    password,
    confirmation,
    error,
    pending,
    groups,
    groupsStatus,
    groupsError,
    setUsername,
    setEmail,
    setGroupId,
    setPassword,
    setConfirmation,
    submit,
    retryGroups: () => {
      setGroupsStatus('loading')
      setGroupsError('')
      setGroupsAttempt((value) => value + 1)
    },
  }
}
