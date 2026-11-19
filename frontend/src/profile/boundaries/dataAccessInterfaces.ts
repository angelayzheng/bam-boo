import type { UserProfileProgressInput } from '../../entities/userProfileProgress'

export interface UserProfileData extends UserProfileProgressInput {
  userId: number
  username: string
  avatar: string
}

export interface ProfileGateway {
  loadProfile(userId: number, signal: AbortSignal): Promise<UserProfileData>
}
