export const levelPath = (date: string) => `/levels/${date}`
export const resultsPath = (date: string) => `${levelPath(date)}/complete`

export type Route = 'home' | 'level' | 'results'

export function getRoute(pathname: string, date: string): Route {
  if (pathname === levelPath(date)) return 'level'
  if (pathname === resultsPath(date)) return 'results'
  return 'home'
}
