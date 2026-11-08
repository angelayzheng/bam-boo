export type Screen = 'home' | 'challenge' | 'results'

export interface ConversationNode {
  type: 'question' | 'response'
  node_key?: string
  transcript_url: string
  audio_url: string
  text: string
  children: ConversationNode[]
}

export interface ChallengeSummary {
  name: string
  slug: string
  challenge_date: string
  difficulty: number
  category: string
}

export interface Challenge extends ChallengeSummary {
  required_action: string
  conversation_tree: ConversationNode
}

export interface ResultData {
  challengeSlug: string
  attemptId: string
  completedAt: string
  toneCorrect: boolean
  toneTime: number
  actionCorrect: boolean
  userId?: number | null
}

export type ScoreSaveState =
  | { status: 'saving' }
  | { status: 'saved' }
  | { status: 'error'; message: string }
