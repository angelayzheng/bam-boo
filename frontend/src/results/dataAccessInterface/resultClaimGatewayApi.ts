import { ApiError, postJson } from '../../dataAccessInterface/httpClient.ts'
import {
  ResultClaimError,
  type ResultClaimGateway,
  type ResultClaimResponse,
} from '../boundaries/dataAccessInterfaces.ts'

const fallbackMessage = 'Could not save your score. Please try again.'

async function claimAttempt(
  attemptId: string,
  challengeSlug: string,
  signal: AbortSignal,
): Promise<ResultClaimResponse> {
  try {
    return await postJson<ResultClaimResponse>(
      `/api/users/me/scores/${encodeURIComponent(challengeSlug)}/`,
      { attempt_id: attemptId },
      signal,
      fallbackMessage,
    )
  } catch (error) {
    if (error instanceof ApiError && error.status === 401) {
      throw new ResultClaimError(
        error.message || 'Authentication required.',
        'unauthorized',
      )
    }
    throw new ResultClaimError(
      error instanceof Error && error.message ? error.message : fallbackMessage,
      'failed',
    )
  }
}

export const resultClaimApi: ResultClaimGateway = {
  claimAttempt,
}
