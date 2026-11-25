import { useCallback, useEffect, useMemo, useState } from 'react'
import HomePage from './pages/homePage'
import ChallengePage from './pages/challengePage'
import ResultsPage from './pages/resultsPage'
import AuthPage from './pages/authPage'
import ProfilePage from './pages/profilePage'
import { authApi } from './auth/dataAccessInterface/authGatewayApi'
import { RestoreSessionInteractor } from './auth/useCases/restoreSession/restoreSessionInteractor'
import { RestoreSessionPresenter } from './auth/useCases/restoreSession/restoreSessionPresenter'
import type { AuthUser } from './entities/types'
import { loadChallengeSummaries } from './challenge/dataAccessInterface/challengeGatewayApi'
import { selectHomeChallenge } from './entities/dailyChallenge'
import {
  challengePath,
  getRoute,
  parseChallengePath,
  resultsPath,
} from './routes'
import type { ChallengeSummary, ResultData } from './entities/types'
import { useResultsFlow } from './pages/useResultsFlow'

function App() {
  const [pathname, setPathname] = useState(() => window.location.pathname)
  const [summaries, setSummaries] = useState<ChallengeSummary[]>([])
  const [todayChallenge, setTodayChallenge] = useState<ChallengeSummary | null>(
    null,
  )
  const [error, setError] = useState('')
  const [attempt, setAttempt] = useState(0)
  const [user, setUser] = useState<AuthUser | null>(null)
  const [authLoading, setAuthLoading] = useState(true)
  const [authError, setAuthError] = useState('')
  const [authAttempt, setAuthAttempt] = useState(0)
  const [progressVersion, setProgressVersion] = useState(0)

  const route = getRoute(pathname)
  const challengeRoute = parseChallengePath(pathname)
  const handleProgressSaved = useCallback(() => {
    setProgressVersion((value) => value + 1)
  }, [])
  const handleUnauthorized = useCallback(() => {
    setUser(null)
  }, [])
  const results = useResultsFlow({
    slug: challengeRoute?.results ? challengeRoute.slug : null,
    user,
    sessionLoading: authLoading,
    onProgressSaved: handleProgressSaved,
    onUnauthorized: handleUnauthorized,
  })

  const restoreSession = useMemo(
    () =>
      new RestoreSessionInteractor(
        authApi,
        new RestoreSessionPresenter((viewModel) => {
          if (viewModel.status === 'error') {
            setAuthError(viewModel.message)
            setAuthLoading(false)
            return
          }
          setUser(viewModel.user)
          setAuthError('')
          setAuthLoading(false)
        }),
      ),
    [],
  )

  useEffect(() => {
    const controller = new AbortController()
    void restoreSession.execute({ signal: controller.signal })
    return () => controller.abort()
  }, [restoreSession, authAttempt])

  useEffect(() => {
    const controller = new AbortController()
    loadChallengeSummaries(controller.signal)
      .then((loaded) => {
        if (controller.signal.aborted) return
        setSummaries(loaded)
        setTodayChallenge(selectHomeChallenge(loaded))
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
    if (!todayChallenge) return
    // Keep the last completion available while its score saves in the background.
    navigate(challengePath(todayChallenge.slug))
  }

  const completeChallenge = (nextResult: ResultData) => {
    results.acceptCompletedResult(nextResult)
    navigate(resultsPath(nextResult.challenge.slug))
  }

  const openAccount = () => navigate(user ? '/profile' : '/login')

  const connecting = authLoading || (!todayChallenge && !error)
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
          progressVersion={progressVersion}
          summaries={summaries}
          user={user}
          onHome={() => navigate('/')}
          onChallenge={todayChallenge ? startChallenge : undefined}
          onLoggedOut={() => {
            setUser(null)
            results.clearResult()
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
          const pendingResult = results.result
          // A guest can claim their pending result when they sign in.
          if (
            pendingResult &&
            !pendingResult.saved &&
            (pendingResult.userId === null ||
              pendingResult.userId === undefined ||
              pendingResult.userId === account.id)
          ) {
            navigate(resultsPath(pendingResult.challenge.slug))
          } else {
            navigate('/profile')
          }
        }}
      />
    )
  }

  if (challengeRoute && !challengeRoute.results) {
    if (authLoading) {
      return (
        <div className="min-h-screen bg-[#f7f8f5] text-slate-900">
          <main className="mx-auto max-w-3xl px-5 py-6 sm:px-8 sm:py-10">
            <div
              role="status"
              className="rounded-xl bg-slate-100 px-4 py-3 text-sm text-slate-600"
            >
              Checking your account before starting the challenge…
            </div>
          </main>
        </div>
      )
    }
    return (
      <ChallengePage
        slug={challengeRoute.slug}
        onExit={() => navigate('/')}
        onComplete={completeChallenge}
      />
    )
  }

  if (challengeRoute?.results) {
    return (
      <ResultsPage
        viewModel={results.resultsViewModel}
        claimViewModel={results.claimViewModel}
        onHome={() => navigate('/')}
        onRetry={() => {
          if (results.result) {
            navigate(challengePath(results.result.challenge.slug))
          } else {
            navigate('/')
          }
        }}
        onRetryClaim={results.retryClaim}
        onLogin={() => navigate('/login')}
        onProfile={() => navigate('/profile')}
      />
    )
  }

  return (
    <HomePage
      challenge={todayChallenge}
      summaries={summaries}
      progressVersion={progressVersion}
      notice={notice}
      onStart={startChallenge}
      onHome={() => navigate('/')}
      user={user}
      accountLoading={authLoading}
      onAccount={openAccount}
    />
  )
}

export default App
