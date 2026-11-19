import type { AuthUser, ResultData } from '../../entities/types'
import type { AuthCredentials } from '../../entities/authCredentials'

export type { AuthCredentials }

export interface SignupGroup {
  id: number
  name: string
}

export interface SessionGateway {
  restoreSession(signal: AbortSignal): Promise<AuthUser | null>
}

export interface AuthenticationGateway {
  authenticate(
    action: 'login' | 'signup',
    credentials: AuthCredentials,
    signal?: AbortSignal,
  ): Promise<AuthUser>
}

export interface LogoutGateway {
  logout(signal?: AbortSignal): Promise<void>
}

export interface SignupGroupGateway {
  loadGroups(signal: AbortSignal): Promise<SignupGroup[]>
}

export interface ScoreSaveResponse {
  user_id: number
  username: string
  avatar: string
  total_score: number
  completed_challenges: number
  scores: Record<string, number>
  attempt: {
    id: number
    attempt_id: string
    challenge_slug: string
    score: number
    completed_at: string
    received_at: string
  }
}

export interface ScoreGateway {
  saveChallengeResult(
    result: ResultData,
    signal: AbortSignal,
  ): Promise<ScoreSaveResponse>
}
