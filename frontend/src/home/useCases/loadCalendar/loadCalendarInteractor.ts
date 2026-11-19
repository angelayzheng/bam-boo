import { buildTrainingCalendar } from '../../../entities/trainingCalendar.ts'
import type { HomeProfileGateway } from '../../boundaries/dataAccessInterfaces'
import type {
  LoadCalendarInputBoundary,
  LoadCalendarInputData,
  LoadCalendarOutputBoundary,
} from './loadCalendarBoundaries'

export class LoadCalendarInteractor implements LoadCalendarInputBoundary {
  private readonly gateway: HomeProfileGateway
  private readonly output: LoadCalendarOutputBoundary

  constructor(gateway: HomeProfileGateway, output: LoadCalendarOutputBoundary) {
    this.gateway = gateway
    this.output = output
  }

  async execute(input: LoadCalendarInputData): Promise<void> {
    if (input.signal.aborted) return
    try {
      const progress = input.username
        ? await this.gateway.loadProgress(input.username, input.signal)
        : { scores: {}, loginDays: [] }
      if (input.signal.aborted) return
      this.output.present({
        status: 'ready',
        calendar: buildTrainingCalendar({
          summaries: input.summaries,
          scores: progress.scores,
          loginDays: progress.loginDays,
          referenceDate: input.referenceDate,
          progressKnown: input.username !== null,
        }),
      })
    } catch (error) {
      if (input.signal.aborted) return
      this.output.present({
        status: 'error',
        message:
          error instanceof Error
            ? error.message
            : 'Could not load your progress.',
        calendar: buildTrainingCalendar({
          summaries: input.summaries,
          scores: {},
          loginDays: [],
          referenceDate: input.referenceDate,
          progressKnown: false,
        }),
      })
    }
  }
}
