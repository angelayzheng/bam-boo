import { useEffect, useMemo, useState } from 'react'
import type { AuthUser, ResultData } from '../entities/types'
import { resultClaimApi } from '../results/dataAccessInterface/resultClaimGatewayApi'
import { resultStorage } from '../results/dataAccessInterface/resultStorageService'
import type {
  ResultClaimViewModel,
  ResultsViewModel,
} from '../results/viewModels/resultsViewModel'
import {
  initialResultClaimViewModel,
  initialResultsViewModel,
  toResultClaimViewModel,
} from '../results/viewModels/resultsViewModel'
import { ClaimChallengeResultInteractor } from '../results/useCases/claimChallengeResult/claimChallengeResultInteractor'
import { ClaimChallengeResultPresenter } from '../results/useCases/claimChallengeResult/claimChallengeResultPresenter'
import { RestoreChallengeResultInteractor } from '../results/useCases/restoreChallengeResult/restoreChallengeResultInteractor'
import { RestoreChallengeResultPresenter } from '../results/useCases/restoreChallengeResult/restoreChallengeResultPresenter'

interface UseResultsFlowArgs {
  slug: string | null
  user: AuthUser | null
  sessionLoading: boolean
  onProgressSaved: () => void
  onUnauthorized: () => void
}

export function useResultsFlow({
  slug,
  user,
  sessionLoading,
  onProgressSaved,
  onUnauthorized,
}: UseResultsFlowArgs): {
  result: ResultData | null
  resultsViewModel: ResultsViewModel
  claimViewModel: ResultClaimViewModel
  acceptCompletedResult: (result: ResultData) => void
  retryClaim: () => void
  clearResult: () => void
} {
  const [result, setResult] = useState<ResultData | null>(null)
  const [resultsViewModel, setResultsViewModel] = useState<ResultsViewModel>(
    initialResultsViewModel,
  )
  const [claimViewModel, setClaimViewModel] = useState<ResultClaimViewModel>(
    initialResultClaimViewModel,
  )
  const [claimAttempt, setClaimAttempt] = useState(0)

  const restore = useMemo(
    () =>
      new RestoreChallengeResultInteractor(
        resultStorage,
        new RestoreChallengeResultPresenter(setResultsViewModel, setResult),
      ),
    [],
  )

  const claim = useMemo(
    () =>
      new ClaimChallengeResultInteractor(
        resultClaimApi,
        resultStorage,
        new ClaimChallengeResultPresenter(
          setClaimViewModel,
          (claimedResult) => {
            setResult(claimedResult)
            onProgressSaved()
          },
          () => onUnauthorized(),
        ),
      ),
    [onProgressSaved, onUnauthorized],
  )

  useEffect(() => {
    if (result && (slug === null || result.challenge.slug === slug)) return
    restore.execute({ slug, seed: null })
  }, [restore, slug, result])

  useEffect(() => {
    if (!result) return
    const controller = new AbortController()
    void claim.execute({
      result,
      user,
      sessionLoading,
      signal: controller.signal,
    })
    return () => controller.abort()
  }, [claim, result, user, sessionLoading, claimAttempt])

  return {
    result,
    resultsViewModel,
    claimViewModel,
    acceptCompletedResult: (completedResult) => {
      restore.execute({
        slug: completedResult.challenge.slug,
        seed: completedResult,
      })
    },
    retryClaim: () => {
      setClaimViewModel(toResultClaimViewModel({ status: 'saving' }))
      setClaimAttempt((value) => value + 1)
    },
    clearResult: () => {
      resultStorage.clear()
      setResult(null)
      setResultsViewModel(initialResultsViewModel())
      setClaimViewModel(initialResultClaimViewModel())
    },
  }
}
