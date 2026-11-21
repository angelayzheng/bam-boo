import test from 'node:test'
import assert from 'node:assert/strict'
import { emptyCalendarEntries } from '../src/entities/calendarEntry.ts'
import {
  initialCalendarViewModel,
  toCalendarViewModelFromEntries,
} from '../src/home/viewModels/homeViewModel.ts'

const summary = {
  name: 'Forgot Password x3',
  slug: 'forgot-password-x3',
  challenge_date: '2026-10-15',
  difficulty: 1,
  category: 'account',
}

test('emptyCalendarEntries covers every day of the month, leap years included', () => {
  const entries = emptyCalendarEntries({ year: 2028, month: 2 })
  assert.equal(entries.length, 29)
  assert.equal(entries[0].date, '2028-02-01')
  assert.equal(entries[28].date, '2028-02-29')
  assert.ok(entries.every((e) => e.status === 'none' && e.challenge === null))
})

test('the calendar view model pads a Sunday-first grid and shows server values', () => {
  const month = { year: 2026, month: 10 }
  const entries = emptyCalendarEntries(month)
  entries[13] = {
    date: '2026-10-14',
    status: 'missed',
    stars: null,
    challenge: { ...summary, challenge_date: '2026-10-14' },
  }
  entries[14] = {
    date: '2026-10-15',
    status: 'completed',
    stars: 2,
    challenge: summary,
  }

  const vm = toCalendarViewModelFromEntries(month, entries, 3)

  assert.equal(vm.monthLabel, 'October 2026')
  assert.equal(vm.streak, 3)
  assert.equal(vm.days.length, 35) // Oct 1, 2026 is a Thursday: 4 blanks + 31 days
  assert.ok(vm.days.slice(0, 4).every((d) => d.day === null && !d.inMonth))
  assert.equal(vm.days[4].day, 1)
  assert.equal(vm.days[17].missed, true)
  assert.equal(vm.days[17].score, null)
  assert.equal(vm.days[18].day, 15)
  assert.equal(vm.days[18].score, 2)
  assert.equal(vm.days[18].hasChallenge, true)
  assert.equal(vm.days[18].missed, false)
})

test('the initial calendar view model is an empty month with no streak', () => {
  const vm = initialCalendarViewModel('2026-10-15')
  assert.equal(vm.status, 'ready')
  assert.equal(vm.streak, 0)
  assert.ok(
    vm.days
      .filter((d) => d.inMonth)
      .every((d) => !d.hasChallenge && d.score === null),
  )
})
