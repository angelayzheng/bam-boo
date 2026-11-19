import type { AuthUser } from '../../entities/types'
import type { UserProfileProgress } from '../../entities/userProfileProgress'
import { formatChallengeDate } from '../../viewModels/challengeDatePresenter.ts'
import type { UserProfileData } from '../boundaries/dataAccessInterfaces'

const AVATARS: Record<string, string> = {
  fox: '🦊',
  owl: '🦉',
  bear: '🐻',
  cat: '🐱',
  robot: '🤖',
  ghost: '👻',
}

export interface ProfileScoreViewModel {
  slug: string
  name: string
  dateLabel: string
  score: number
  scoreLabel: string
}

export interface ProfileViewModel {
  status: 'loading' | 'ready' | 'error'
  username: string
  email: string
  avatarEmoji: string
  totalScore: number | null
  completedChallenges: number | null
  scores: ProfileScoreViewModel[]
  message: string
}

export function initialProfileViewModel(user: AuthUser): ProfileViewModel {
  return {
    status: 'loading',
    username: user.username,
    email: user.email,
    avatarEmoji: '👤',
    totalScore: null,
    completedChallenges: null,
    scores: [],
    message: '',
  }
}

export function toProfileViewModel(
  profile: UserProfileData,
  progress: UserProfileProgress,
  user: AuthUser,
): ProfileViewModel {
  return {
    status: 'ready',
    username: user.username,
    email: user.email,
    avatarEmoji: AVATARS[profile.avatar] ?? '👤',
    totalScore: progress.totalScore,
    completedChallenges: progress.completedChallenges,
    scores: progress.scores.map((row) => ({
      slug: row.slug,
      name: row.name,
      dateLabel: row.challengeDate
        ? formatChallengeDate(row.challengeDate)
        : '',
      score: row.score,
      scoreLabel: `${row.score} / 3`,
    })),
    message: '',
  }
}

export function errorProfileViewModel(
  message: string,
  user: AuthUser,
): ProfileViewModel {
  return {
    ...initialProfileViewModel(user),
    status: 'error',
    message,
  }
}
