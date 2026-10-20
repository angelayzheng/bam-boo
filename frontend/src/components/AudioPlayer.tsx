import { useEffect, useRef, useState } from 'react'
import type { ConversationNode } from '../types'

interface AudioPlayerProps {
  node: ConversationNode
  label: string
  autoPlay?: boolean
  onEnded?: () => void
}

export default function AudioPlayer({
  node,
  label,
  autoPlay = false,
  onEnded,
}: AudioPlayerProps) {
  const audio = useRef<HTMLAudioElement>(null)
  const [failed, setFailed] = useState(false)

  useEffect(() => {
    if (autoPlay) {
      // Browsers can require a manual press of Play before allowing autoplay.
      void audio.current?.play().catch(() => {})
    }
  }, [autoPlay])

  useEffect(() => {
    const player = audio.current
    return () => player?.pause()
  }, [])

  return (
    <section
      className={`rounded-3xl border p-5 shadow-sm sm:p-6 ${node.type === 'response' ? 'border-[#bdebdc] bg-[#eefbf6]' : 'border-slate-200 bg-white'}`}
    >
      <p className="mb-3 text-sm font-bold text-[#17243d]">{label}</p>
      <p className="mb-4 text-sm leading-6 text-slate-700">{node.text}</p>
      <audio
        ref={audio}
        controls
        preload="metadata"
        src={node.audio_url}
        aria-label={`${label} recording`}
        className="h-10 w-full"
        onPlay={() => {
          document.querySelectorAll('audio').forEach((player) => {
            if (player !== audio.current) player.pause()
          })
        }}
        onEnded={onEnded}
        onError={() => setFailed(true)}
      />
      {failed && (
        <p role="alert" className="mt-3 text-sm text-red-700">
          This audio could not be loaded. You can follow the transcript above.
        </p>
      )}
    </section>
  )
}
