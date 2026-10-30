import Header from '../components/Header'
import { CheckIcon, StarIcon } from '../components/icons'
import { challengeDateLabel } from '../challenges'
import type { Challenge, ResultData } from '../types'

interface ResultsPageProps {
  challenge: Challenge
  result: ResultData
  onHome: () => void
  onRetry: () => void
}

export default function ResultsPage({
  challenge,
  result,
  onHome,
  onRetry,
}: ResultsPageProps) {
  const achievements = [
    {
      earned: result.toneCorrect,
      title: 'Read the tone',
      detail: result.toneCorrect
        ? `You recognized the customer was ${challenge.tone}.`
        : `Expected tone: ${challenge.tone}.`,
    },
    {
      earned: result.toneTime <= 10,
      title: 'Quick instinct',
      detail:
        result.toneTime <= 10
          ? `Tone identified in ${result.toneTime} seconds.`
          : `Tone identified in ${result.toneTime} seconds. Aim for 10.`,
    },
    {
      earned: result.actionCorrect,
      title: 'Correct next step',
      detail: `${result.actionCorrect ? 'You identified the next step' : 'Expected next step'}: ${challenge.required_action}.`,
    },
  ]
  const stars = achievements.filter(({ earned }) => earned).length

  return (
    <div className="bg-beige min-h-screen text-black">
      <Header compact />
      <main className="mx-auto flex max-w-3xl flex-col items-center px-5 py-12 text-center sm:px-8 sm:py-16">
        <div className="bg-green-dark shadow-card grid size-16 place-items-center rounded-3xl text-white">
          <CheckIcon className="size-8" />
        </div>
        <p className="text-green-dark mt-7 text-sm font-bold tracking-[0.18em] uppercase">
          Challenge complete
        </p>
        <h1 className="text-orange mt-3 text-4xl font-extrabold sm:text-5xl">
          {stars === 3 ? 'Beautifully handled.' : 'Good work. Keep listening.'}
        </h1>
        <p className="mt-4 max-w-lg text-lg leading-7 text-black/70">
          “{challenge.name}” · {challengeDateLabel(challenge)}
        </p>

        <div
          className="my-9 flex gap-3"
          aria-label={`${stars} out of 3 stars earned`}
        >
          {[0, 1, 2].map((index) => (
            <StarIcon
              key={index}
              className={`size-13 drop-shadow-md sm:size-16 ${index < stars ? 'text-green-light' : 'text-green-pale'}`}
            />
          ))}
        </div>

        <div className="grid w-full gap-3 text-left sm:grid-cols-3">
          {achievements.map((achievement) => (
            <div
              key={achievement.title}
              className={`shadow-card rounded-2xl border p-5 ${achievement.earned ? 'border-green-light bg-green-pale/50' : 'border-black/10 bg-white/40'}`}
            >
              <div
                className={`mb-4 grid size-8 place-items-center rounded-full ${achievement.earned ? 'bg-green-dark text-white' : 'bg-black/10 text-black/40'}`}
              >
                {achievement.earned ? (
                  <CheckIcon className="size-4" />
                ) : (
                  <span className="text-sm font-bold">—</span>
                )}
              </div>
              <h2 className="text-lg font-bold">{achievement.title}</h2>
              <p className="mt-1.5 text-sm leading-5 text-black/70">
                {achievement.detail}
              </p>
            </div>
          ))}
        </div>

        <div className="mt-8 flex w-full flex-col gap-3 sm:flex-row sm:justify-center">
          <button
            type="button"
            onClick={onHome}
            className="from-orange to-olive focus-visible:outline-green-dark rounded-xl bg-linear-to-b px-6 py-3.5 text-base font-bold text-white transition hover:brightness-105 focus-visible:outline-3 focus-visible:outline-offset-2"
          >
            Back to calendar
          </button>
          <button
            type="button"
            onClick={onRetry}
            className="border-green-dark text-green-dark hover:bg-green-pale/50 focus-visible:outline-green-dark rounded-xl border-2 px-6 py-3.5 text-base font-bold transition focus-visible:outline-3 focus-visible:outline-offset-2"
          >
            Retry challenge
          </button>
        </div>
      </main>
    </div>
  )
}
