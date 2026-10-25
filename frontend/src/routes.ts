export const challengePath = (date: string) => `/challenges/${date}`
export const resultsPath = (date: string) => `${challengePath(date)}/complete`

export type Route = 'home' | 'challenge' | 'results'

export function getRoute(pathname: string, date: string): Route {
  if (pathname === challengePath(date)) return 'challenge'
  if (pathname === resultsPath(date)) return 'results'
  return 'home'
}
