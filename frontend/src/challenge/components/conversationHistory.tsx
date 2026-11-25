import AudioPlayer from './AudioPlayer'
import type { ChallengeAudioTurnViewModel } from '../viewModels/challengeViewModel'

interface ConversationHistoryProps {
  path: ChallengeAudioTurnViewModel[]
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
            key={node.transcriptUrl}
            className={
              node.type === 'response' ? 'ml-6 sm:ml-12' : 'mr-6 sm:mr-12'
            }
          >
            <AudioPlayer
              node={node}
              label={
                node.type === 'question' ? 'Customer' : 'You · Support agent'
              }
              autoPlay={activeAudio === node.transcriptUrl}
              onEnded={() => onAudioEnded(node.transcriptUrl)}
            />
          </li>
        ))}
      </ol>
    </section>
  )
}
