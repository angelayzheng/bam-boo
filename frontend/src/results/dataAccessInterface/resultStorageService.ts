import type { ResultData } from '../../entities/types'
import type { ResultStorage } from '../boundaries/dataAccessInterfaces'

const RESULT_STORAGE_KEY = 'bam-boo:last-challenge-result'

export const resultStorage: ResultStorage = {
  load: () => {
    try {
      const saved = window.sessionStorage.getItem(RESULT_STORAGE_KEY)
      if (!saved) return null
      return JSON.parse(saved) as unknown
    } catch {
      try {
        window.sessionStorage.removeItem(RESULT_STORAGE_KEY)
      } catch {
        // Session storage can be unavailable; there is nothing to clear.
      }
      return null
    }
  },
  save: (result: ResultData) => {
    try {
      window.sessionStorage.setItem(RESULT_STORAGE_KEY, JSON.stringify(result))
    } catch {
      // The in-memory result still supports this navigation.
    }
  },
  clear: () => {
    try {
      window.sessionStorage.removeItem(RESULT_STORAGE_KEY)
    } catch {
      // Session storage can be unavailable; there is nothing to clear.
    }
  },
}
