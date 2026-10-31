export const challengePath = (date: string) => `/challenges/${date}`
export const resultsPath = (date: string) => `${challengePath(date)}/complete`

export type Route =
  'home' | 'challenge' | 'results' | 'login' | 'signup' | 'profile'

export function getRoute(pathname: string, date?: string): Route {
  if (pathname === '/login') return 'login'
  if (pathname === '/signup') return 'signup'
  if (pathname === '/profile') return 'profile'
  if (!date) return 'home'
  if (pathname === challengePath(date)) return 'challenge'
  if (pathname === resultsPath(date)) return 'results'
  return 'home'
}
