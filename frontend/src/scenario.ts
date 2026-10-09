import scenario from '../../data/sample-scenario.json'

export const levelDate = new Date(`${scenario.date}T00:00:00`)
export const levelDateLabel = new Intl.DateTimeFormat('en-CA', {
  weekday: 'long',
  month: 'long',
  day: 'numeric',
  year: 'numeric',
}).format(levelDate)

export default scenario
