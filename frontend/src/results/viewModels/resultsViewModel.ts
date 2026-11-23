import {
  resultOutcomes,
  type ResultOutcomes,
} from '../../entities/challengeResultSummary.ts'
import type { ResultData } from '../../entities/types.ts'
import { challengeDateLabel } from '../../viewModels/challengeDatePresenter.ts'
import type { ClaimChallengeResultOutputData } from '../useCases/claimChallengeResult/claimChallengeResultBoundaries'

export interface AchievementViewModel {
  earned: boolean
  title: string
  detail: string
}

export type ResultsViewModel =
  | { status: 'loading'; message: string }
  | { status: 'unavailable'; message: string }
  | {
      status: 'ready'
      challengeName: string
      dateLabel: string
      heading: string
      starCount: number
      stars: boolean[]
      achievements: AchievementViewModel[]
    }

export type ResultClaimStatus =
  | 'checking'
  | 'guest'
  | 'saving'
  | 'saved'
  | 'error'
  | 'other-account'
  | 'invalid'
  | 'unauthorized'

export interface ResultClaimViewModel {
  status: ResultClaimStatus
  message: string
  showLogin: boolean
  showProfile: boolean
  canRetry: boolean
}

export function initialResultsViewModel(): ResultsViewModel {
  return { status: 'loading', message: 'Loading your result…' }
}

export function unavailableResultsViewModel(message: string): ResultsViewModel {
  return { status: 'unavailable', message }
}

export function toResultsViewModel(result: ResultData): ResultsViewModel {
  const outcomes = resultOutcomes(result)
  return {
    status: 'ready',
    challengeName: result.challenge.name,
    dateLabel: challengeDateLabel(result.challenge),
    heading:
      outcomes.stars === 3
        ? 'Beautifully handled.'
        : 'Good work. Keep listening.',
    starCount: outcomes.stars,
    stars: [0, 1, 2].map((index) => index < outcomes.stars),
    achievements: achievementsFor(result, outcomes),
  }
}

function achievementsFor(
  result: ResultData,
  outcomes: ResultOutcomes,
): AchievementViewModel[] {
  const toneTime = Math.round(result.toneTime)
  return [
    {
      earned: outcomes.tone,
      title: 'Read the tone',
      detail: outcomes.tone
        ? 'You recognized the customer’s emotional tone.'
        : 'Your answer did not match the customer’s emotional tone.',
    },
    {
      earned: outcomes.speed,
      title: 'Quick instinct',
      detail: outcomes.speed
        ? `Tone identified in ${toneTime} seconds.`
        : `Tone identified in ${toneTime} seconds. Aim for 10.`,
    },
    {
      earned: outcomes.action,
      title: 'Correct next step',
      detail: `${outcomes.action ? 'You identified the next step' : 'Expected next step'}: ${result.requiredAction}.`,
    },
  ]
}

export function initialResultClaimViewModel(): ResultClaimViewModel {
  return {
    status: 'checking',
    message: 'Checking your account before saving…',
    showLogin: false,
    showProfile: false,
    canRetry: false,
  }
}

export function toResultClaimViewModel(
  output: ClaimChallengeResultOutputData,
): ResultClaimViewModel {
  const empty = {
    showLogin: false,
    showProfile: false,
    canRetry: false,
  }
  switch (output.status) {
    case 'checking':
      return {
        ...empty,
        status: 'checking',
        message: 'Checking your account before saving…',
      }
    case 'guest':
      return {
        ...empty,
        status: 'guest',
        message: 'Your result is kept in this browser session.',
        showLogin: true,
      }
    case 'saving':
      return { ...empty, status: 'saving', message: 'Saving your score…' }
    case 'saved':
      return {
        ...empty,
        status: 'saved',
        message: 'Score saved to your profile. Your best score counts.',
        showProfile: true,
      }
    case 'error':
      return {
        ...empty,
        status: 'error',
        message: output.message.startsWith('Could not save your score.')
          ? output.message
          : `Could not save your score. ${output.message}`,
        canRetry: true,
      }
    case 'other-account':
      return {
        ...empty,
        status: 'other-account',
        message:
          'This result belongs to another session. Retry the challenge to save a score to this account.',
      }
    case 'invalid':
      return {
        ...empty,
        status: 'invalid',
        message:
          'This result has no completion details. Retry the challenge to record a new completion.',
      }
    case 'unauthorized':
      return {
        ...empty,
        status: 'unauthorized',
        message: 'Your session expired. Log in to save your score.',
        showLogin: true,
      }
  }
}
