import { useEffect, useState } from 'react'
import HomePage from './pages/HomePage'
import LevelPage from './pages/LevelPage'
import ResultsPage from './pages/ResultsPage'
import { getRoute, levelPath, resultsPath } from './routes'
import type { ResultData } from './types'

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
    window.speechSynthesis?.cancel()
    setResult(null)
    window.sessionStorage.removeItem(RESULT_STORAGE_KEY)
    navigate(levelPath)
  }

  const completeLevel = (nextResult: ResultData) => {
    window.speechSynthesis?.cancel()
    setResult(nextResult)
    window.sessionStorage.setItem(RESULT_STORAGE_KEY, JSON.stringify(nextResult))
    navigate(resultsPath)
  }

  if (getRoute(pathname) === 'level') {
    return <LevelPage onExit={() => navigate('/')} onComplete={completeLevel} />
  }

  if (getRoute(pathname) === 'results' && result) {
    return <ResultsPage result={result} onHome={() => navigate('/')} onRetry={startLevel} />
  }

  return <HomePage onStart={startLevel} />
}

export default App
