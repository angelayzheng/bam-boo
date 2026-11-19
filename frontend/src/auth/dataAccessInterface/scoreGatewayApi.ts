import type { ResultData } from '../../entities/types'
import type {
  ScoreGateway,
  ScoreSaveResponse,
} from '../boundaries/dataAccessInterfaces'
import { postJson } from './httpClient.ts'

async function saveChallengeResult(
  result: ResultData,
  signal: AbortSignal,
): Promise<ScoreSaveResponse> {
  return postJson<ScoreSaveResponse>(
    `/api/users/me/scores/${encodeURIComponent(result.challengeSlug)}/`,
    {
      tone_correct: result.toneCorrect,
      tone_time: result.toneTime,
      action_correct: result.actionCorrect,
      attempt_id: result.attemptId,
      completed_at: result.completedAt,
    },
    signal,
  )
}

export const scoreApi: ScoreGateway = {
  saveChallengeResult,
}
