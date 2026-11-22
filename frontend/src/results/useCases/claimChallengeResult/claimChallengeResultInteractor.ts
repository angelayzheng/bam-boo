import {
  claimEligibility,
  markResultClaimed,
} from '../../../entities/challengeResultSummary.ts'
import {
  ResultClaimError,
  type ResultClaimGateway,
  type ResultStorage,
} from '../../boundaries/dataAccessInterfaces.ts'
import type {
  ClaimChallengeResultInputBoundary,
  ClaimChallengeResultInputData,
  ClaimChallengeResultOutputBoundary,
} from './claimChallengeResultBoundaries.ts'

const fallbackMessage = 'Could not save your score. Please try again.'

export class ClaimChallengeResultInteractor implements ClaimChallengeResultInputBoundary {
  private readonly gateway: ResultClaimGateway
  private readonly storage: ResultStorage
  private readonly output: ClaimChallengeResultOutputBoundary

  constructor(
    gateway: ResultClaimGateway,
    storage: ResultStorage,
    output: ClaimChallengeResultOutputBoundary,
  ) {
    this.gateway = gateway
    this.storage = storage
    this.output = output
  }

  async execute(input: ClaimChallengeResultInputData): Promise<void> {
    const eligibility = claimEligibility(
      input.result,
      input.user,
      input.sessionLoading,
    )
    if (eligibility === 'saved') {
      this.output.present({
        status: 'saved',
        result: input.result,
        claimed: false,
      })
      return
    }
    if (eligibility !== 'claimable') {
      this.output.present({ status: eligibility })
      return
    }
    if (!input.user) {
      this.output.present({ status: 'guest' })
      return
    }

    this.output.present({ status: 'saving' })
    if (input.signal.aborted) return
    try {
      await this.gateway.claimAttempt(
        input.result.attemptId,
        input.result.challenge.slug,
        input.signal,
      )
      if (input.signal.aborted) return
      const updated = markResultClaimed(input.result, input.user.id)
      this.storage.save(updated)
      this.output.present({
        status: 'saved',
        result: updated,
        claimed: true,
      })
    } catch (error) {
      if (input.signal.aborted) return
      if (isUnauthorized(error)) {
        this.output.present({ status: 'unauthorized' })
        return
      }
      this.output.present({
        status: 'error',
        message: error instanceof Error ? error.message : fallbackMessage,
      })
    }
  }
}

function isUnauthorized(error: unknown): boolean {
  return error instanceof ResultClaimError && error.reason === 'unauthorized'
}
