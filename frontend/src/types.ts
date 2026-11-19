export type Screen = 'home' | 'challenge' | 'results'

export type ScoreSaveState =
  | { status: 'saving' }
  | { status: 'saved' }
  | { status: 'error'; message: string }
