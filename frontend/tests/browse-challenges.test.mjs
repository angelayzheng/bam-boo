import assert from 'node:assert/strict'
import test from 'node:test'
import { shiftMonth } from '../src/entities/calendarEntry.ts'
import { BrowseChallengesInteractor } from '../src/home/useCases/browseChallenges/browseChallengesInteractor.ts'
import { BrowseChallengesPresenter } from '../src/home/useCases/browseChallenges/browseChallengesPresenter.ts'

const entry = (date, status = 'none') => ({
  date,
  status,
  stars: null,
  challenge: null,
})

const recorder = () => {
  const outputs = []
  return {
    outputs,
    boundary: {
      present(output) {
        outputs.push(output)
      },
    },
  }
}

const gatewayReturning = (entries) => {
  const calls = []
  return {
    calls,
    async browseChallenges(month, signal) {
      calls.push({ month, signal })
      return entries
    },
  }
}

test('browseChallenges presents the entries for the requested month', async () => {
  const { outputs, boundary } = recorder()
  const entries = [entry('2026-10-01'), entry('2026-10-02', 'missed')]
  const gateway = gatewayReturning(entries)
  const signal = new AbortController().signal
  const month = { year: 2026, month: 10 }

  await new BrowseChallengesInteractor(gateway, boundary).execute({
    month,
    signal,
  })

  assert.equal(gateway.calls.length, 1)
  assert.deepEqual(gateway.calls[0].month, month)
  assert.equal(gateway.calls[0].signal, signal)
  assert.deepEqual(outputs, [{ status: 'ready', month, entries }])
})

test('browseChallenges rejects an invalid month without calling the gateway', async () => {
  const { outputs, boundary } = recorder()
  const gateway = gatewayReturning([])
  const month = { year: 2026, month: 13 }

  await new BrowseChallengesInteractor(gateway, boundary).execute({
    month,
    signal: new AbortController().signal,
  })

  assert.equal(gateway.calls.length, 0)
  assert.equal(outputs.length, 1)
  assert.equal(outputs[0].status, 'error')
  assert.equal(outputs[0].message, 'Month must be between 1 and 12.')
  assert.deepEqual(outputs[0].entries, [])
})

test('browseChallenges reports gateway failures with empty entries', async () => {
  const { outputs, boundary } = recorder()
  const interactor = new BrowseChallengesInteractor(
    {
      async browseChallenges() {
        throw new Error('calendar unavailable')
      },
    },
    boundary,
  )

  await interactor.execute({
    month: { year: 2026, month: 10 },
    signal: new AbortController().signal,
  })

  assert.equal(outputs.length, 1)
  assert.equal(outputs[0].status, 'error')
  assert.equal(outputs[0].message, 'calendar unavailable')
  assert.deepEqual(outputs[0].entries, [])
})

test('browseChallenges falls back to a generic message for unknown errors', async () => {
  const { outputs, boundary } = recorder()
  const interactor = new BrowseChallengesInteractor(
    {
      async browseChallenges() {
        throw 'boom'
      },
    },
    boundary,
  )

  await interactor.execute({
    month: { year: 2026, month: 10 },
    signal: new AbortController().signal,
  })

  assert.equal(outputs[0].message, 'Could not load the calendar.')
})

test('browseChallenges skips requests that are already aborted', async () => {
  const { outputs, boundary } = recorder()
  const controller = new AbortController()
  controller.abort()
  const gateway = gatewayReturning([])

  await new BrowseChallengesInteractor(gateway, boundary).execute({
    month: { year: 2026, month: 10 },
    signal: controller.signal,
  })

  assert.equal(gateway.calls.length, 0)
  assert.equal(outputs.length, 0)
})

test('browseChallenges presents nothing when aborted while loading', async () => {
  const { outputs, boundary } = recorder()
  const controller = new AbortController()
  const interactor = new BrowseChallengesInteractor(
    {
      async browseChallenges() {
        controller.abort()
        return [entry('2026-10-01')]
      },
    },
    boundary,
  )

  await interactor.execute({
    month: { year: 2026, month: 10 },
    signal: controller.signal,
  })

  assert.equal(outputs.length, 0)
})

test('browseChallenges presenter passes through entries and clears the error', () => {
  const results = []
  const presenter = new BrowseChallengesPresenter((result) =>
    results.push(result),
  )
  const month = { year: 2026, month: 10 }
  const entries = [entry('2026-10-01')]

  presenter.present({ status: 'ready', month, entries })
  presenter.present({ status: 'error', month, message: 'nope', entries: [] })

  assert.deepEqual(results, [
    { month, entries, error: '' },
    { month, entries: [], error: 'nope' },
  ])
})

test('shiftMonth moves across year boundaries in both directions', () => {
  assert.deepEqual(shiftMonth({ year: 2026, month: 12 }, 1), {
    year: 2027,
    month: 1,
  })
  assert.deepEqual(shiftMonth({ year: 2026, month: 1 }, -1), {
    year: 2025,
    month: 12,
  })
  assert.deepEqual(shiftMonth({ year: 2026, month: 5 }, 0), {
    year: 2026,
    month: 5,
  })
})
