import type { ChallengeSession } from '../entities/challengeSession.ts'

export interface SessionStore {
  get(): ChallengeSession | null
  set(session: ChallengeSession): void
}

export function createSessionStore(): SessionStore {
  let session: ChallengeSession | null = null
  return {
    get: () => session,
    set: (value) => {
      session = value
    },
  }
}
