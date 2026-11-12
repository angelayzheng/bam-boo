import AudioPlayer from '../AudioPlayer'
import type { ConversationNode } from '../../types'

interface ConversationHistoryProps {
  path: ConversationNode[]
  activeAudio: string
  onAudioEnded: (transcriptUrl: string) => void
}

export default function ConversationHistory({
  path,
  activeAudio,
  onAudioEnded,
}: ConversationHistoryProps) {
  return (
    <section className="mb-6" aria-label="Conversation history">
      <h2 className="mb-4 text-2xl font-bold">Your conversation</h2>
      <ol className="grid gap-4" aria-live="polite" aria-relevant="additions">
        {path.map((node) => (
          <li
            key={node.transcript_url}
            className={
              node.type === 'response' ? 'ml-6 sm:ml-12' : 'mr-6 sm:mr-12'
            }
          >
            <AudioPlayer
              node={node}
              label={
                node.type === 'question' ? 'Customer' : 'You · Support agent'
              }
              autoPlay={activeAudio === node.transcript_url}
              onEnded={() => onAudioEnded(node.transcript_url)}
            />
          </li>
        ))}
      </ol>
    </section>
  )
}
