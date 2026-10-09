import { useCallback, useEffect, useRef, useState } from 'react'
import { PauseIcon, PlayIcon } from './icons'

interface AudioPlayerProps {
  text: string
  label: string
  autoPlay?: boolean
}

export default function AudioPlayer({ text, label, autoPlay = false }: AudioPlayerProps) {
  const [playing, setPlaying] = useState(false)
  const [progress, setProgress] = useState(0)
  const startedAt = useRef(0)
  const duration = Math.max(7, Math.round(text.split(' ').length / 2.4))

  const stop = useCallback(() => {
    window.speechSynthesis.cancel()
    setPlaying(false)
  }, [])

  const play = useCallback(() => {
    if (!('speechSynthesis' in window)) return

    window.speechSynthesis.cancel()
    const utterance = new SpeechSynthesisUtterance(text)
    utterance.rate = 0.96
    utterance.pitch = 0.95
    utterance.onend = () => {
      setPlaying(false)
      setProgress(100)
    }
    utterance.onerror = () => setPlaying(false)
    startedAt.current = Date.now()
    setProgress(0)
    setPlaying(true)
    window.speechSynthesis.speak(utterance)
  }, [text])

  useEffect(() => {
    if (!autoPlay) return

    const timer = window.setTimeout(play, 450)
    return () => window.clearTimeout(timer)
  }, [autoPlay, play])

  useEffect(() => {
    if (!playing) return

    const timer = window.setInterval(() => {
      const elapsed = (Date.now() - startedAt.current) / 1000
      setProgress(Math.min(96, (elapsed / duration) * 100))
    }, 200)
    return () => window.clearInterval(timer)
  }, [duration, playing])

  useEffect(() => stop, [stop])

  return (
    <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-[0_16px_45px_-28px_rgba(15,23,42,0.35)] sm:p-6">
      <div className="flex items-center gap-4">
        <button type="button" onClick={playing ? stop : play} className="grid size-13 shrink-0 place-items-center rounded-full bg-[#17243d] text-white transition hover:scale-105 hover:bg-[#223253] focus-visible:outline-3 focus-visible:outline-offset-3 focus-visible:outline-[#66d9b7]" aria-label={playing ? 'Pause customer audio' : 'Play customer audio'}>
          {playing ? <PauseIcon /> : <PlayIcon className="ml-0.5 size-5" />}
        </button>
        <div className="min-w-0 flex-1">
          <div className="mb-3 flex items-center justify-between gap-4">
            <div>
              <p className="text-sm font-semibold text-slate-900">{label}</p>
              <p className="text-xs text-slate-500">Customer · {duration} sec</p>
            </div>
            <span className="shrink-0 rounded-full bg-[#eefbf6] px-2.5 py-1 text-xs font-semibold text-[#167c61]">{playing ? 'Playing' : progress === 100 ? 'Replay' : 'Ready'}</span>
          </div>
          <div className="h-1.5 overflow-hidden rounded-full bg-slate-100">
            <div className="h-full rounded-full bg-[#29b88e] transition-[width] duration-200" style={{ width: `${progress}%` }} />
          </div>
        </div>
      </div>
    </section>
  )
}
