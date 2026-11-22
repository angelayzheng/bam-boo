import type {
  ScoreGateway,
  ScoreSaveResponse,
} from '../boundaries/dataAccessInterfaces'
import { postJson } from '../../dataAccessInterface/httpClient.ts'

async function claimAttempt(
  attemptId: string,
  challengeSlug: string,
  signal: AbortSignal,
): Promise<ScoreSaveResponse> {
  return postJson<ScoreSaveResponse>(
    `/api/users/me/scores/${encodeURIComponent(challengeSlug)}/`,
    { attempt_id: attemptId },
    signal,
  )
}

export const scoreApi: ScoreGateway = {
  claimAttempt,
}
