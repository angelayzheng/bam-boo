import { selectHomeChallenge } from '../../../entities/dailyChallenge.ts'
import type {
  LoadTodayChallengeInputBoundary,
  LoadTodayChallengeInputData,
  LoadTodayChallengeOutputBoundary,
} from './loadTodayChallengeBoundaries'

export class LoadTodayChallengeInteractor implements LoadTodayChallengeInputBoundary {
  private readonly output: LoadTodayChallengeOutputBoundary

  constructor(output: LoadTodayChallengeOutputBoundary) {
    this.output = output
  }

  execute(input: LoadTodayChallengeInputData): void {
    this.output.present({ challenge: selectHomeChallenge(input.summaries) })
  }
}
