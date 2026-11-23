import test from 'node:test'
import assert from 'node:assert/strict'
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

test('the calendar view model pads a Sunday-first grid and shows server values', () => {
  const month = { year: 2026, month: 10 }
  const entries = [
    {
      date: '2026-10-14',
      status: 'missed',
      stars: null,
      challenge: { ...summary, challenge_date: '2026-10-14' },
    },
    { date: '2026-10-15', status: 'completed', stars: 2, challenge: summary },
  ]

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

test('entries are placed by date even when unsorted', () => {
  const month = { year: 2026, month: 10 }
  const entries = [
    { date: '2026-10-15', status: 'completed', stars: 3, challenge: summary },
    {
      date: '2026-10-02',
      status: 'missed',
      stars: null,
      challenge: { ...summary, challenge_date: '2026-10-02' },
    },
  ]
  const vm = toCalendarViewModelFromEntries(
    month,
    entries,
    0,
    'ready',
    '',
    '2026-10-15',
  )
  const day = (n) => vm.days.find((d) => d.day === n)
  assert.equal(day(15).score, 3)
  assert.equal(day(15).isToday, true)
  assert.equal(day(2).missed, true)
  assert.equal(day(3).hasChallenge, false)
})

test('a short or empty entry list still renders the whole month', () => {
  const vm = toCalendarViewModelFromEntries({ year: 2026, month: 10 }, [], 0)
  assert.equal(vm.days.filter((d) => d.inMonth).length, 31)
})
