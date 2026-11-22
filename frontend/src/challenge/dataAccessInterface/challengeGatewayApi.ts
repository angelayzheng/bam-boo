import type { ChallengeSummary } from '../../entities/types'
import { getJson } from '../../dataAccessInterface/httpClient.ts'

const fallbackMessage =
  'Could not load the recording. Check that the Django backend is running.'

export async function loadChallengeSummaries(
  signal: AbortSignal,
): Promise<ChallengeSummary[]> {
  const { challenges } = await getJson<{ challenges: ChallengeSummary[] }>(
    '/api/challenges/',
    signal,
    fallbackMessage,
  )
  return challenges
}
