import type { AttemptStorage } from '../boundaries/dataAccessInterfaces'

const key = (slug: string) => `bam-boo:challenge-attempt:${slug}`

export const attemptStorage: AttemptStorage = {
  load: (slug) => {
    try {
      return window.sessionStorage.getItem(key(slug))
    } catch {
      return null
    }
  },
  save: (slug, attemptId) => {
    try {
      window.sessionStorage.setItem(key(slug), attemptId)
    } catch {
      // Session storage can be unavailable; the attempt still works in memory.
    }
  },
  clear: (slug) => {
    try {
      window.sessionStorage.removeItem(key(slug))
    } catch {
      // Session storage can be unavailable; there is nothing to clear.
    }
  },
}
