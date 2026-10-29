import { useEffect, useState } from 'react'
import HomePage from './pages/HomePage'
import ChallengePage from './pages/ChallengePage'
import ResultsPage from './pages/ResultsPage'
import AuthPage from './pages/AuthPage'
import ProfilePage from './pages/ProfilePage'
import { getCurrentUser, signOut } from './auth'
import type { AuthUser } from './auth'
import { loadChallenge } from './challenges'
import { challengePath, getRoute, resultsPath } from './routes'
import type { Challenge, ResultData } from './types'

const RESULT_STORAGE_KEY = 'bam-boo:last-challenge-result'

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
  const [user, setUser] = useState<AuthUser | null>(null)
  const [authLoading, setAuthLoading] = useState(true)
  const [authError, setAuthError] = useState('')
  const [authAttempt, setAuthAttempt] = useState(0)

  useEffect(() => {
    const controller = new AbortController()
    getCurrentUser(controller.signal)
      .then((account) => {
        if (!controller.signal.aborted) setUser(account)
      })
      .catch((cause: unknown) => {
        if (!controller.signal.aborted)
          setAuthError(
            cause instanceof Error
              ? cause.message
              : 'Could not check your account.',
          )
      })
      .finally(() => {
        if (!controller.signal.aborted) setAuthLoading(false)
      })
    return () => controller.abort()
  }, [authAttempt])

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

  const startChallenge = () => {
    if (!challenge) return
    setResult(null)
    window.sessionStorage.removeItem(RESULT_STORAGE_KEY)
    navigate(challengePath(challenge.challenge_date))
  }

  const completeChallenge = (nextResult: ResultData) => {
    if (!challenge) return
    setResult(nextResult)
    window.sessionStorage.setItem(
      RESULT_STORAGE_KEY,
      JSON.stringify(nextResult),
    )
    navigate(resultsPath(challenge.challenge_date))
  }

  const route = getRoute(pathname, challenge?.challenge_date)
  const openAccount = () => navigate(user ? '/profile' : '/login')

  const connecting = authLoading || (!challenge && !error)
  const notice =
    error || authError || connecting ? (
      <div
        role="status"
        className="mb-6 flex flex-wrap items-center justify-between gap-2 rounded-xl bg-slate-100 px-4 py-3 text-xs leading-relaxed text-slate-600"
      >
        <p>
          {error && authError
            ? 'Make sure the Django backend is running to load recordings and account details.'
            : error ||
              (authError
                ? 'Account services are unavailable. Make sure the Django backend is running.'
                : 'Connecting to recordings and account services…')}
        </p>
        {(error || authError) && (
          <button
            type="button"
            disabled={connecting}
            onClick={() => {
              if (error) {
                setError('')
                setAttempt((value) => value + 1)
              }
              if (authError) {
                setAuthError('')
                setAuthLoading(true)
                setAuthAttempt((value) => value + 1)
              }
            }}
            className="shrink-0 font-semibold text-[#176d59] underline underline-offset-4 disabled:opacity-50"
          >
            {connecting ? 'Connecting…' : 'Retry connection'}
          </button>
        )}
      </div>
    ) : undefined

  if (route === 'login' || route === 'signup' || route === 'profile') {
    if (user)
      return (
        <ProfilePage
          key={user.id}
          notice={notice}
          user={user}
          onHome={() => navigate('/')}
          onLogout={async () => {
            await signOut()
            setUser(null)
            setResult(null)
            window.sessionStorage.removeItem(RESULT_STORAGE_KEY)
            navigate('/login')
          }}
        />
      )
    return (
      <AuthPage
        key={route}
        notice={notice}
        sessionLoading={authLoading}
        mode={route === 'signup' ? 'signup' : 'login'}
        onNavigate={navigate}
        onAuthenticated={(account) => {
          setUser(account)
          setAuthError('')
          navigate('/profile')
        }}
      />
    )
  }

  if (challenge && route === 'challenge') {
    return (
      <ChallengePage
        challenge={challenge}
        onExit={() => navigate('/')}
        onComplete={completeChallenge}
      />
    )
  }

  if (
    challenge &&
    route === 'results' &&
    result?.challengeId === challenge.id
  ) {
    return (
      <ResultsPage
        challenge={challenge}
        result={result}
        onHome={() => navigate('/')}
        onRetry={startChallenge}
      />
    )
  }

  return (
    <HomePage
      challenge={challenge}
      notice={notice}
      onStart={startChallenge}
      user={user}
      accountLoading={authLoading}
      onAccount={openAccount}
    />
  )
}

export default App
