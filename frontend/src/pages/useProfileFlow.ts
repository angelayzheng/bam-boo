import { useEffect, useMemo, useState } from 'react'
import { authApi } from '../auth/dataAccessInterface/authGatewayApi'
import { initialLogoutViewModel } from '../auth/viewModels/authViewModel'
import { LogoutUserInteractor } from '../auth/useCases/logoutUser/logoutUserInteractor'
import { LogoutUserPresenter } from '../auth/useCases/logoutUser/logoutUserPresenter'
import type { AuthUser } from '../entities/types'
import type { ChallengeSummary } from '../entities/types'
import { profileGateway } from '../profile/dataAccessInterface/profileGatewayApi'
import type { ProfileViewModel } from '../profile/viewModels/profileViewModel'
import { initialProfileViewModel } from '../profile/viewModels/profileViewModel'
import { LoadUserProfileInteractor } from '../profile/useCases/loadUserProfile/loadUserProfileInteractor'
import { LoadUserProfilePresenter } from '../profile/useCases/loadUserProfile/loadUserProfilePresenter'

interface UseProfileFlowArgs {
  user: AuthUser
  summaries: ChallengeSummary[]
  progressVersion: number
  onLoggedOut: () => void
}

export function useProfileFlow({
  user,
  summaries,
  progressVersion,
  onLoggedOut,
}: UseProfileFlowArgs): {
  viewModel: ProfileViewModel
  retry: () => void
  logout: () => void
  loggingOut: boolean
  logoutError: string
} {
  const [viewModel, setViewModel] = useState(() =>
    initialProfileViewModel(user),
  )
  const [attempt, setAttempt] = useState(0)
  const [logoutViewModel, setLogoutViewModel] = useState(initialLogoutViewModel)

  const interactor = useMemo(
    () =>
      new LoadUserProfileInteractor(
        profileGateway,
        new LoadUserProfilePresenter(setViewModel, user),
      ),
    [user],
  )

  const logoutUseCase = useMemo(
    () =>
      new LogoutUserInteractor(
        authApi,
        new LogoutUserPresenter((nextViewModel) => {
          setLogoutViewModel(nextViewModel)
          if (nextViewModel.status === 'ready') onLoggedOut()
        }),
      ),
    [onLoggedOut],
  )

  useEffect(() => {
    const controller = new AbortController()
    void interactor.execute({
      userId: user.id,
      summaries,
      signal: controller.signal,
    })
    return () => controller.abort()
  }, [interactor, user.id, summaries, progressVersion, attempt])

  return {
    viewModel,
    retry: () => setAttempt((value) => value + 1),
    logout: () => {
      setLogoutViewModel({ status: 'pending', message: '' })
      void logoutUseCase.execute({})
    },
    loggingOut: logoutViewModel.status === 'pending',
    logoutError:
      logoutViewModel.status === 'error' ? logoutViewModel.message : '',
  }
}
