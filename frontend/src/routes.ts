const challengePattern = /^\/challenges\/([A-Za-z0-9_-]+)(\/complete)?$/

export interface ChallengeRoute {
  slug: string
  results: boolean
}

export function parseChallengePath(pathname: string): ChallengeRoute | null {
  const match = challengePattern.exec(pathname)
  if (!match) return null
  return { slug: match[1], results: Boolean(match[2]) }
}

export const challengePath = (slug: string) =>
  `/challenges/${encodeURIComponent(slug)}`
export const resultsPath = (slug: string) => `${challengePath(slug)}/complete`

export type Route =
  'home' | 'challenge' | 'results' | 'login' | 'signup' | 'profile'

export function getRoute(pathname: string): Route {
  if (pathname === '/login') return 'login'
  if (pathname === '/signup') return 'signup'
  if (pathname === '/profile') return 'profile'
  const challenge = parseChallengePath(pathname)
  if (!challenge) return 'home'
  return challenge.results ? 'results' : 'challenge'
}
