import { useEffect, useRef, useState } from 'react'
import AudioPlayer from '../components/AudioPlayer'
import Header from '../components/Header'
import { ArrowLeftIcon, CheckIcon } from '../components/icons'
import scenario, { levelDateLabel } from '../scenario'
import type { ResultData } from '../types'

type Stage = 'tone' | 'response' | 'action'

interface LevelPageProps {
  onExit: () => void
  onComplete: (result: ResultData) => void
}

export default function LevelPage({ onExit, onComplete }: LevelPageProps) {
  const [stage, setStage] = useState<Stage>('tone')
  const [tone, setTone] = useState('')
  const [toneTime, setToneTime] = useState(0)
  const [toneCorrect, setToneCorrect] = useState(false)
  const [selectedResponse, setSelectedResponse] = useState<number | null>(null)
  const [nextAction, setNextAction] = useState('')
  const startedAt = useRef(0)

  useEffect(() => {
    startedAt.current = Date.now()
  }, [])

  const submitTone = () => {
    const elapsed = Math.max(1, Math.round((Date.now() - startedAt.current) / 1000))
    const normalized = tone.toLowerCase().trim()
    setToneTime(elapsed)
    setToneCorrect(scenario.toneAnswers.some((answer) => normalized.includes(answer)))
    setStage('response')
  }

  const submitAction = () => {
    const normalized = nextAction.toLowerCase()
    const mentionsCard = normalized.includes('card')
    const mentionsSecure = ['lock', 'freeze', 'block', 'cancel', 'secure', 'replace'].some((word) => normalized.includes(word))
    const mentionsFraud = ['fraud', 'dispute', 'unauthorized', 'investigation', 'claim'].some((word) => normalized.includes(word))
    onComplete({ toneCorrect, toneTime, actionCorrect: mentionsCard && (mentionsSecure || mentionsFraud) })
  }

  const stepNumber = stage === 'tone' ? 1 : stage === 'response' ? 2 : 3

  return (
    <div className="min-h-screen bg-[#f7f8f5] text-slate-900">
      <Header compact />
      <main className="mx-auto max-w-3xl px-5 py-6 sm:px-8 sm:py-10">
        <div className="mb-7 flex items-center justify-between">
          <button type="button" onClick={onExit} className="flex items-center gap-1.5 text-sm font-semibold text-slate-500 transition hover:text-slate-900"><ArrowLeftIcon /> Exit level</button>
          <span className="text-right text-xs font-bold tracking-[0.12em] text-[#19856a] uppercase">Level {scenario.level} · {levelDateLabel}</span>
        </div>

        <div className="mb-8">
          <div className="mb-2 flex justify-between text-xs font-semibold text-slate-500"><span>Step {stepNumber} of 3</span><span>{Math.round((stepNumber / 3) * 100)}%</span></div>
          <div className="h-1.5 overflow-hidden rounded-full bg-slate-200"><div className="h-full rounded-full bg-[#29b88e] transition-all duration-500" style={{ width: `${(stepNumber / 3) * 100}%` }} /></div>
        </div>

        <div className="mb-6">
          <p className="text-xs font-bold tracking-[0.14em] text-[#cf6029] uppercase">{scenario.category}</p>
          <h1 className="mt-2 text-3xl font-bold tracking-[-0.025em] text-[#17243d] sm:text-4xl">{scenario.title}</h1>
        </div>

        {stage === 'tone' && (
          <div className="animate-[fade-in_.35s_ease-out]">
            <AudioPlayer text={scenario.opening} label="Opening statement" autoPlay />
            <section className="mt-6 rounded-3xl border border-slate-200 bg-white p-6 sm:p-8">
              <p className="text-xs font-bold tracking-[0.15em] text-[#19856a] uppercase">Listen for what is underneath</p>
              <h2 className="mt-2 text-2xl font-bold tracking-tight text-[#17243d]">What is the customer’s emotional tone?</h2>
              <p className="mt-2 text-sm leading-6 text-slate-500">Use one or two words. Your first instinct is usually best.</p>
              <form className="mt-6" onSubmit={(event) => { event.preventDefault(); if (tone.trim()) submitTone() }}>
                <label htmlFor="tone" className="sr-only">Customer tone</label>
                <input id="tone" value={tone} onChange={(event) => setTone(event.target.value.split(/\s+/).slice(0, 2).join(' '))} placeholder="e.g. concerned" autoComplete="off" autoFocus className="w-full rounded-2xl border-2 border-slate-200 bg-[#fbfcfa] px-4 py-4 text-lg font-medium text-slate-900 outline-none transition placeholder:text-slate-300 focus:border-[#29b88e] focus:ring-4 focus:ring-[#29b88e]/10" />
                <div className="mt-4 flex items-center justify-between gap-4">
                  <p className="text-xs text-slate-400">1–2 words only</p>
                  <button type="submit" disabled={!tone.trim()} className="rounded-xl bg-[#17243d] px-5 py-3 text-sm font-bold text-white transition hover:bg-[#223253] disabled:cursor-not-allowed disabled:opacity-35">Lock in answer</button>
                </div>
              </form>
            </section>
          </div>
        )}

        {stage === 'response' && (
          <div className="animate-[fade-in_.35s_ease-out]">
            <div className="mb-5 rounded-2xl border border-[#bdebdc] bg-[#eefbf6] px-4 py-3 text-sm text-[#176d59]"><span className="font-bold">Tone captured:</span> {tone} · {toneTime} seconds</div>
            <AudioPlayer text={scenario.customerReply} label="Customer follow-up" autoPlay />
            <section className="mt-6 rounded-3xl border border-slate-200 bg-white p-6 sm:p-8">
              <p className="text-xs font-bold tracking-[0.15em] text-[#19856a] uppercase">Listen and respond</p>
              <h2 className="mt-2 text-2xl font-bold tracking-tight text-[#17243d]">What would you ask next?</h2>
              <p className="mt-2 text-sm leading-6 text-slate-500">Choose the response that moves the call forward with care.</p>
              <div className="mt-6 grid gap-3" role="radiogroup" aria-label="Follow-up response">
                {scenario.responses.map((response, index) => (
                  <button key={response} type="button" role="radio" aria-checked={selectedResponse === index} onClick={() => setSelectedResponse(index)} className={`flex items-start gap-4 rounded-2xl border-2 p-4 text-left transition ${selectedResponse === index ? 'border-[#29b88e] bg-[#eefbf6]' : 'border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50'}`}>
                    <span className={`mt-0.5 grid size-6 shrink-0 place-items-center rounded-full border-2 ${selectedResponse === index ? 'border-[#29b88e] bg-[#29b88e] text-white' : 'border-slate-300'}`}>{selectedResponse === index && <CheckIcon className="size-3.5" />}</span>
                    <span className="text-sm leading-6 font-medium text-slate-700">{response}</span>
                  </button>
                ))}
              </div>
              <div className="mt-6 flex justify-end"><button type="button" disabled={selectedResponse === null} onClick={() => setStage('action')} className="rounded-xl bg-[#17243d] px-5 py-3 text-sm font-bold text-white transition hover:bg-[#223253] disabled:cursor-not-allowed disabled:opacity-35">Continue</button></div>
            </section>
          </div>
        )}

        {stage === 'action' && (
          <section className="animate-[fade-in_.35s_ease-out] rounded-3xl border border-slate-200 bg-white p-6 shadow-[0_16px_45px_-28px_rgba(15,23,42,0.35)] sm:p-8">
            <div className="grid size-12 place-items-center rounded-2xl bg-[#fff0e8] text-[#cf6029]"><CheckIcon className="size-6" /></div>
            <p className="mt-6 text-xs font-bold tracking-[0.15em] text-[#19856a] uppercase">Close the loop</p>
            <h2 className="mt-2 text-2xl font-bold tracking-tight text-[#17243d]">What action will you take next?</h2>
            <p className="mt-2 max-w-xl text-sm leading-6 text-slate-500">Write the next operational step you would take after this conversation.</p>
            <form className="mt-6" onSubmit={(event) => { event.preventDefault(); if (nextAction.trim()) submitAction() }}>
              <label htmlFor="next-action" className="sr-only">Next action</label>
              <textarea id="next-action" rows={4} value={nextAction} onChange={(event) => setNextAction(event.target.value)} placeholder="e.g. Freeze the card and open a fraud claim..." autoFocus className="w-full resize-none rounded-2xl border-2 border-slate-200 bg-[#fbfcfa] px-4 py-4 text-base leading-6 text-slate-900 outline-none transition placeholder:text-slate-300 focus:border-[#29b88e] focus:ring-4 focus:ring-[#29b88e]/10" />
              <div className="mt-4 flex justify-end"><button type="submit" disabled={!nextAction.trim()} className="rounded-xl bg-[#17243d] px-6 py-3 text-sm font-bold text-white transition hover:bg-[#223253] disabled:cursor-not-allowed disabled:opacity-35">Finish level</button></div>
            </form>
          </section>
        )}
      </main>
    </div>
  )
}
