export interface ChallengeSummary {
  name: string
  slug: string
  challenge_date: string
  difficulty: number
  category: string
}

export type AttemptStatus = 'tone' | 'conversation' | 'action' | 'completed'

export interface AttemptTurn {
  id: string
  type: 'question' | 'response'
  transcriptUrl: string
  audioUrl: string
  text: string
}

export interface AttemptChoice extends AttemptTurn {
  choiceId: string
}

export interface AttemptSnapshot {
  attemptId: string
  stage: AttemptStatus
  challenge: ChallengeSummary
  opening: AttemptTurn
  conversation: AttemptTurn[]
  choices: AttemptChoice[]
  toneCorrect: boolean | null
  toneTime: number | null
  toneSpeedCorrect: boolean | null
  toneSimilarity: number | null
  actionCorrect: boolean | null
  score: number | null
  requiredAction: string | null
  completedAt: string | null
}

export interface ResultData {
  attemptId: string
  challenge: ChallengeSummary
  completedAt: string
  toneCorrect: boolean
  toneTime: number
  toneSpeedCorrect: boolean
  toneSimilarity: number | null
  actionCorrect: boolean
  score: number
  requiredAction: string
  userId?: number | null
  saved?: boolean
}

export interface AuthUser {
  id: number
  username: string
  email: string
}
