import Header from '../components/Header'
import { CheckIcon, StarIcon } from '../components/icons'
import scenario, { levelDateLabel } from '../scenario'
import type { ResultData } from '../types'

interface ResultsPageProps {
  result: ResultData
  onHome: () => void
  onRetry: () => void
}

export default function ResultsPage({ result, onHome, onRetry }: ResultsPageProps) {
  const achievements = [
    {
      earned: result.toneCorrect,
      title: 'Read the tone',
      detail: result.toneCorrect ? 'You recognized the customer was anxious.' : 'Expected an anxious or concerned tone.',
    },
    {
      earned: result.toneTime <= 10,
      title: 'Quick instinct',
      detail: result.toneTime <= 10 ? `Identified in ${result.toneTime} seconds.` : `Identified in ${result.toneTime} seconds. Aim for 10.`,
    },
    {
      earned: result.actionCorrect,
      title: 'Right next step',
      detail: result.actionCorrect ? 'You protected the card and started the dispute process.' : scenario.actionHint,
    },
  ]
  const stars = achievements.filter(({ earned }) => earned).length

  return (
    <div className="min-h-screen bg-[#17243d] text-white">
      <Header compact />
      <main className="mx-auto flex max-w-3xl flex-col items-center px-5 py-12 text-center sm:px-8 sm:py-16">
        <div className="grid size-16 place-items-center rounded-3xl bg-[#75e2c1] text-[#17243d] shadow-xl shadow-black/15"><CheckIcon className="size-8" /></div>
        <p className="mt-7 text-xs font-bold tracking-[0.18em] text-[#75e2c1] uppercase">Level complete</p>
        <h1 className="mt-3 text-4xl font-bold tracking-[-0.035em] sm:text-5xl">{stars === 3 ? 'Beautifully handled.' : 'Good work. Keep listening.'}</h1>
        <p className="mt-4 max-w-lg text-base leading-7 text-slate-300">“{scenario.title}” · {levelDateLabel}</p>

        <div className="my-9 flex gap-3" aria-label={`${stars} out of 3 stars earned`}>
          {[0, 1, 2].map((index) => <StarIcon key={index} className={`size-13 drop-shadow-lg sm:size-16 ${index < stars ? 'text-[#ffc857]' : 'text-slate-600'}`} />)}
        </div>

        <div className="grid w-full gap-3 text-left sm:grid-cols-3">
          {achievements.map((achievement) => (
            <div key={achievement.title} className={`rounded-2xl border p-5 ${achievement.earned ? 'border-[#75e2c1]/25 bg-white/10' : 'border-white/10 bg-white/5'}`}>
              <div className={`mb-4 grid size-8 place-items-center rounded-full ${achievement.earned ? 'bg-[#75e2c1] text-[#17243d]' : 'bg-slate-700 text-slate-400'}`}>{achievement.earned ? <CheckIcon className="size-4" /> : <span className="text-sm font-bold">—</span>}</div>
              <h2 className="text-sm font-bold text-white">{achievement.title}</h2>
              <p className="mt-1.5 text-xs leading-5 text-slate-300">{achievement.detail}</p>
            </div>
          ))}
        </div>

        <div className="mt-8 flex w-full flex-col gap-3 sm:flex-row sm:justify-center">
          <button type="button" onClick={onHome} className="rounded-xl bg-[#75e2c1] px-6 py-3.5 text-sm font-bold text-[#17243d] transition hover:bg-[#90ebd0]">Back to calendar</button>
          <button type="button" onClick={onRetry} className="rounded-xl border border-white/20 px-6 py-3.5 text-sm font-bold text-white transition hover:bg-white/10">Retry level</button>
        </div>
      </main>
    </div>
  )
}
