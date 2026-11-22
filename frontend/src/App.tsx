import { useEffect, useMemo, useState } from 'react'
import HomePage from './pages/HomePage'
import ChallengePage from './pages/ChallengePage'
import ResultsPage from './pages/ResultsPage'
import AuthPage from './pages/AuthPage'
import ProfilePage from './pages/ProfilePage'
import { authApi } from './auth/dataAccessInterface/authGatewayApi'
import { scoreApi } from './auth/dataAccessInterface/scoreGatewayApi'
import { ApiError } from './dataAccessInterface/httpClient'
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
import type { ScoreSaveState } from './types'

const RESULT_STORAGE_KEY = 'bam-boo:last-challenge-result'

function isChallengeSummary(value: unknown): value is ChallengeSummary {
  if (typeof value !== 'object' || value === null) return false
  const candidate = value as ChallengeSummary
  return (
    typeof candidate.name === 'string' &&
    typeof candidate.slug === 'string' &&
    typeof candidate.challenge_date === 'string' &&
    typeof candidate.difficulty === 'number' &&
    typeof candidate.category === 'string'
  )
}

function loadSavedResult(): ResultData | null {
  try {
    const saved = window.sessionStorage.getItem(RESULT_STORAGE_KEY)
    if (!saved) return null
    const parsed: unknown = JSON.parse(saved)
    if (typeof parsed !== 'object' || parsed === null) {
      window.sessionStorage.removeItem(RESULT_STORAGE_KEY)
      return null
    }
    const result = parsed as Partial<ResultData>
    if (
      typeof result.attemptId !== 'string' ||
      !result.attemptId ||
      typeof result.completedAt !== 'string' ||
      !result.completedAt ||
      typeof result.toneCorrect !== 'boolean' ||
      typeof result.toneTime !== 'number' ||
      !Number.isFinite(result.toneTime) ||
      typeof result.toneSpeedCorrect !== 'boolean' ||
      typeof result.actionCorrect !== 'boolean' ||
      typeof result.score !== 'number' ||
      !Number.isInteger(result.score) ||
      result.score < 0 ||
      result.score > 3 ||
      typeof result.requiredAction !== 'string' ||
      !isChallengeSummary(result.challenge)
    ) {
      window.sessionStorage.removeItem(RESULT_STORAGE_KEY)
      return null
    }
    return {
      ...(parsed as ResultData),
      userId: result.userId ?? null,
      saved: result.saved === true,
    }
  } catch {
    return null
  }
}

function App() {
  const [pathname, setPathname] = useState(() => window.location.pathname)
  const [result, setResult] = useState<ResultData | null>(loadSavedResult)
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
  const [scoreSave, setScoreSave] = useState<ScoreSaveState>(() =>
    result?.saved ? { status: 'saved' } : { status: 'saving' },
  )
  const [saveAttempt, setSaveAttempt] = useState(0)
  const [progressVersion, setProgressVersion] = useState(0)
  const currentUserId = user?.id

  useEffect(() => {
    if (
      !result ||
      result.saved ||
      !result.attemptId ||
      !result.completedAt ||
      currentUserId === undefined ||
      (result.userId !== null && result.userId !== currentUserId)
    )
      return
    const controller = new AbortController()
    scoreApi
      .claimAttempt(result.attemptId, result.challenge.slug, controller.signal)
      .then(() => {
        if (controller.signal.aborted) return
        setScoreSave({ status: 'saved' })
        setResult((previous) => {
          if (!previous || previous.attemptId !== result.attemptId) {
            return previous
          }
          const savedResult = {
            ...previous,
            userId: currentUserId,
            saved: true,
          }
          try {
            window.sessionStorage.setItem(
              RESULT_STORAGE_KEY,
              JSON.stringify(savedResult),
            )
          } catch {
            // The in-memory result still reflects the saved score.
          }
          return savedResult
        })
        setProgressVersion((value) => value + 1)
      })
      .catch((cause: unknown) => {
        if (controller.signal.aborted) return
        if (cause instanceof ApiError && cause.status === 401) setUser(null)
        setScoreSave({
          status: 'error',
          message:
            cause instanceof Error
              ? cause.message
              : 'Could not save your score. Please try again.',
        })
      })
    return () => controller.abort()
  }, [result, currentUserId, saveAttempt])

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
    const ownedResult: ResultData = {
      ...nextResult,
      userId: user?.id ?? null,
      saved: false,
    }
    setScoreSave({ status: 'saving' })
    setResult(ownedResult)
    window.sessionStorage.setItem(
      RESULT_STORAGE_KEY,
      JSON.stringify(ownedResult),
    )
    navigate(resultsPath(nextResult.challenge.slug))
  }

  const route = getRoute(pathname)
  const challengeRoute = parseChallengePath(pathname)
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
          // A guest can claim their pending result when they sign in.
          if (
            result &&
            !result.saved &&
            (result.userId === null || result.userId === account.id)
          ) {
            const ownedResult = {
              ...result,
              userId: account.id,
              saved: false,
            }
            setScoreSave({ status: 'saving' })
            setResult(ownedResult)
            window.sessionStorage.setItem(
              RESULT_STORAGE_KEY,
              JSON.stringify(ownedResult),
            )
            navigate(resultsPath(result.challenge.slug))
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

  if (
    challengeRoute?.results &&
    result &&
    result.challenge.slug === challengeRoute.slug
  ) {
    return (
      <ResultsPage
        result={result}
        onHome={() => navigate('/')}
        onRetry={() => navigate(challengePath(result.challenge.slug))}
        user={user}
        sessionLoading={authLoading}
        saveState={scoreSave}
        onSaveRetry={() => {
          setScoreSave({ status: 'saving' })
          setSaveAttempt((value) => value + 1)
        }}
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
