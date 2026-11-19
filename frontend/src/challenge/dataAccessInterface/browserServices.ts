import type { Clock, IdGenerator } from '../boundaries/dataAccessInterfaces'

export const browserClock: Clock = {
  now: () => Date.now(),
}

export const browserIds: IdGenerator = {
  randomId: () => crypto.randomUUID(),
}

export function prefersReducedMotion(): boolean {
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches
}

export function scrollIntoView(element: HTMLElement | null): void {
  element?.scrollIntoView({
    behavior: prefersReducedMotion() ? 'auto' : 'smooth',
    block: 'end',
  })
}
