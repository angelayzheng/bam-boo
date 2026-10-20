import { useEffect, useState } from 'react'
import HomePage from './pages/HomePage'
import LevelPage from './pages/LevelPage'
import ResultsPage from './pages/ResultsPage'
import { loadChallenge } from './challenges'
import { getRoute, levelPath, resultsPath } from './routes'
import type { Challenge, ResultData } from './types'

const RESULT_STORAGE_KEY = 'bam-boo:last-level-result'

function loadSavedResult(): ResultData | null {
  try {
    const saved = window.sessionStorage.getItem(RESULT_STORAGE_KEY)
    return saved ? (JSON.parse(saved) as ResultData) : null
  } catch {
    return null
  }
}

function App() {
  const [pathname, setPathname] = useState(() => window.location.pathname)
  const [result, setResult] = useState<ResultData | null>(loadSavedResult)
  const [challenge, setChallenge] = useState<Challenge | null>(null)
  const [error, setError] = useState('')
  const [attempt, setAttempt] = useState(0)

  useEffect(() => {
    const controller = new AbortController()
    loadChallenge(controller.signal)
      .then((loaded) => {
        if (!controller.signal.aborted) setChallenge(loaded)
      })
      .catch((cause: unknown) => {
        if (!controller.signal.aborted) {
          setError(
            cause instanceof Error
              ? cause.message
              : 'Could not load the recording.',
          )
        }
      })
    return () => controller.abort()
  }, [attempt])

  useEffect(() => {
    const updatePathname = () => setPathname(window.location.pathname)
    window.addEventListener('popstate', updatePathname)
    return () => window.removeEventListener('popstate', updatePathname)
  }, [])

  const navigate = (path: string) => {
    window.history.pushState({}, '', path)
    setPathname(path)
    window.scrollTo(0, 0)
  }

  const startLevel = () => {
    if (!challenge) return
    setResult(null)
    window.sessionStorage.removeItem(RESULT_STORAGE_KEY)
    navigate(levelPath(challenge.challenge_date))
  }

  const completeLevel = (nextResult: ResultData) => {
    if (!challenge) return
    setResult(nextResult)
    window.sessionStorage.setItem(
      RESULT_STORAGE_KEY,
      JSON.stringify(nextResult),
    )
    navigate(resultsPath(challenge.challenge_date))
  }

  if (!challenge) {
    return (
      <main className="grid min-h-screen place-content-center gap-4 bg-[#f7f8f5] px-6 text-center text-[#17243d]">
        <h1 className="text-2xl font-bold">
          {error ? 'Recording unavailable' : 'Loading your recording…'}
        </h1>
        <p role={error ? 'alert' : 'status'}>
          {error || 'Getting the conversation from the backend.'}
        </p>
        {error && (
          <button
            type="button"
            onClick={() => {
              setError('')
              setAttempt((value) => value + 1)
            }}
            className="mx-auto rounded-xl bg-[#17243d] px-5 py-3 font-semibold text-white"
          >
            Try again
          </button>
        )}
      </main>
    )
  }

  if (getRoute(pathname, challenge.challenge_date) === 'level') {
    return (
      <LevelPage
        challenge={challenge}
        onExit={() => navigate('/')}
        onComplete={completeLevel}
      />
    )
  }

  if (
    getRoute(pathname, challenge.challenge_date) === 'results' &&
    result?.challengeId === challenge.id
  ) {
    return (
      <ResultsPage
        challenge={challenge}
        result={result}
        onHome={() => navigate('/')}
        onRetry={startLevel}
      />
    )
  }

  return <HomePage challenge={challenge} onStart={startLevel} />
}

export default App
