export async function scoreTone(
  answer: string,
  challengeSlug: string,
  signal: AbortSignal,
): Promise<boolean> {
  const response = await fetch(
    `/api/tone/${encodeURIComponent(challengeSlug)}/?answer=${encodeURIComponent(answer.trim())}`,
    { signal },
  )
  if (response.status === 404) {
    throw new Error(
      'Tone or challenge not recognized. Try another word or phrase.',
    )
  }
  if (!response.ok) {
    throw new Error('Tone scoring is unavailable. Please try again.')
  }
  const result = await response.json()
  if (
    typeof result.similarity !== 'number' ||
    !Number.isFinite(result.similarity) ||
    result.similarity < -1 ||
    result.similarity > 1 ||
    typeof result.correct !== 'boolean'
  ) {
    throw new Error('Tone scoring returned an invalid score. Please try again.')
  }
  return result.correct
}
