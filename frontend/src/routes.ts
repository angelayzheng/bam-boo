import scenario from './scenario'

export const levelPath = `/levels/${scenario.date}`
export const resultsPath = `${levelPath}/complete`

export type Route = 'home' | 'level' | 'results'

export function getRoute(pathname: string): Route {
  if (pathname === levelPath) return 'level'
  if (pathname === resultsPath) return 'results'
  return 'home'
}
