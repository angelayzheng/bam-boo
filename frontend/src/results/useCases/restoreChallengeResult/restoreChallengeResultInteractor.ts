import { parseChallengeResult } from '../../../entities/challengeResultSummary.ts'
import type { ResultData } from '../../../entities/types'
import type { ResultStorage } from '../../boundaries/dataAccessInterfaces'
import type {
  RestoreChallengeResultInputBoundary,
  RestoreChallengeResultInputData,
  RestoreChallengeResultOutputBoundary,
} from './restoreChallengeResultBoundaries.ts'

const unavailableMessage =
  'This result is no longer available. Retry the challenge to record a new completion.'

export class RestoreChallengeResultInteractor implements RestoreChallengeResultInputBoundary {
  private readonly storage: ResultStorage
  private readonly output: RestoreChallengeResultOutputBoundary

  constructor(
    storage: ResultStorage,
    output: RestoreChallengeResultOutputBoundary,
  ) {
    this.storage = storage
    this.output = output
  }

  execute(input: RestoreChallengeResultInputData): void {
    if (input.seed) {
      const seed = parseChallengeResult(input.seed)
      if (seed && matchesSlug(seed, input.slug)) {
        this.storage.save(seed)
        this.output.present({ status: 'ready', result: seed })
        return
      }
    }

    const stored = parseChallengeResult(this.storage.load())
    if (stored && matchesSlug(stored, input.slug)) {
      this.output.present({ status: 'ready', result: stored })
      return
    }
    if (!stored) this.storage.clear()
    this.output.present({
      status: 'unavailable',
      message: unavailableMessage,
    })
  }
}

function matchesSlug(result: ResultData, slug: string | null): boolean {
  return slug === null || result.challenge.slug === slug
}
