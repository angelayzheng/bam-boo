import { useEffect, useState } from 'react'
import type { ReactNode } from 'react'
import Header from '../components/Header'
import { loadProfile } from '../auth'
import type { AuthUser, UserProfile } from '../auth'
import { challengeDateLabel, loadChallengeSummaries } from '../challenges'
import type { ChallengeSummary } from '../types'

interface ProfilePageProps {
  user: AuthUser
  onLogout: () => Promise<void>
  onHome: () => void
  notice?: ReactNode
  progressVersion?: number
}

const avatars: Record<string, string> = {
  fox: '🦊',
  owl: '🦉',
  bear: '🐻',
  cat: '🐱',
  robot: '🤖',
  ghost: '👻',
}

export default function ProfilePage({
  user,
  onLogout,
  onHome,
  notice,
  progressVersion = 0,
}: ProfilePageProps) {
  const [profile, setProfile] = useState<UserProfile | null>(null)
  const [error, setError] = useState('')
  const [attempt, setAttempt] = useState(0)
  const [loggingOut, setLoggingOut] = useState(false)
  const [logoutError, setLogoutError] = useState('')
  const [summaries, setSummaries] = useState<Record<string, ChallengeSummary>>(
    {},
  )

  useEffect(() => {
    const controller = new AbortController()
    loadProfile(user.id, controller.signal)
      .then((loaded) => {
        if (!controller.signal.aborted) {
          setProfile(loaded)
          setError('')
        }
      })
      .catch((cause: unknown) => {
        if (!controller.signal.aborted)
          setError(
            cause instanceof Error
              ? cause.message
              : 'Could not load your profile.',
          )
      })
    return () => controller.abort()
  }, [user.id, attempt, progressVersion])

  useEffect(() => {
    const controller = new AbortController()
    loadChallengeSummaries(controller.signal)
      .then((list) => {
        if (!controller.signal.aborted)
          setSummaries(Object.fromEntries(list.map((c) => [String(c.id), c])))
      })
      .catch(() => {
        // Fall back to "Challenge <id>" if names fail to load.
      })
    return () => controller.abort()
  }, [])

  async function logout() {
    setLoggingOut(true)
    setLogoutError('')
    try {
      await onLogout()
    } catch (cause) {
      setLogoutError(
        cause instanceof Error
          ? cause.message
          : 'Could not log out. Please try again.',
      )
      setLoggingOut(false)
    }
  }

  return (
    <div className="bg-beige min-h-screen text-black">
      <Header user={user} onHome={onHome} />
      <main className="mx-auto max-w-3xl px-5 py-10 sm:py-14">
        {notice}
        <div className="mb-7 flex flex-wrap items-center justify-between gap-4">
          <h1 className="text-orange text-4xl font-extrabold">My Profile</h1>
          <button
            type="button"
            onClick={logout}
            disabled={loggingOut}
            className="border-green-dark text-green-dark hover:bg-green-pale/50 focus-visible:outline-green-dark rounded-xl border-2 px-5 py-3 text-base font-bold transition focus-visible:outline-2 focus-visible:outline-offset-2 disabled:opacity-60"
          >
            {loggingOut ? 'Logging out…' : 'Log out'}
          </button>
        </div>
        {logoutError && (
          <p
            role="alert"
            className="mb-5 rounded-xl bg-red-50 p-4 text-base text-red-800"
          >
            {logoutError}
          </p>
        )}
        <section
          aria-label="Account details"
          className="shadow-card flex items-center gap-5 rounded-2xl bg-white/60 p-6"
        >
          <span
            role="img"
            aria-label={profile ? `${profile.avatar} avatar` : 'Account avatar'}
            className="bg-green-pale grid size-20 shrink-0 place-items-center rounded-2xl text-4xl"
          >
            {profile ? (avatars[profile.avatar] ?? '👤') : '👤'}
          </span>
          <div className="min-w-0">
            <h2 className="text-2xl font-bold break-words">{user.username}</h2>
            <p className="mt-1 text-base break-words text-black/60">
              {user.email || 'No email provided'}
            </p>
          </div>
        </section>
        {error ? (
          <div className="shadow-card mt-6 rounded-2xl bg-white/60 p-5">
            <p role="alert" className="text-base text-red-800">
              {error}
            </p>
            <button
              type="button"
              onClick={() => {
                setError('')
                setAttempt((value) => value + 1)
              }}
              className="text-green-dark mt-3 font-semibold underline underline-offset-4 transition hover:text-black"
            >
              Try again
            </button>
          </div>
        ) : !profile ? (
          <p role="status" className="mt-6 text-black/60">
            Loading your progress…
          </p>
        ) : (
          <>
            <dl className="mt-6 grid grid-cols-2 gap-4">
              <div className="bg-green-pale/50 shadow-card rounded-2xl p-5">
                <dt className="text-base text-black/60">Total score</dt>
                <dd className="mt-2 text-4xl font-extrabold">
                  {profile.total_score}
                </dd>
              </div>
              <div className="bg-green-pale/50 shadow-card rounded-2xl p-5">
                <dt className="text-base text-black/60">
                  Completed challenges
                </dt>
                <dd className="mt-2 text-4xl font-extrabold">
                  {profile.completed_challenges}
                </dd>
              </div>
            </dl>
            <section className="shadow-card mt-6 rounded-2xl bg-white/60 p-6">
              <h2 className="text-2xl font-bold">Best challenge scores</h2>
              {Object.keys(profile.scores).length === 0 ? (
                <p className="mt-3 text-base leading-relaxed text-black/60">
                  No saved scores yet. Complete a challenge while logged in to
                  start tracking your progress.
                </p>
              ) : (
                <table className="mt-4 w-full text-left text-base">
                  <thead>
                    <tr className="border-green-light border-b text-black/60">
                      <th scope="col" className="py-3 font-medium">
                        Challenge
                      </th>
                      <th scope="col" className="py-3 text-right font-medium">
                        Best score
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(profile.scores).map(([id, score]) => {
                      const info = summaries[id]
                      return (
                        <tr
                          key={id}
                          className="border-green-pale border-b last:border-0"
                        >
                          <th scope="row" className="py-3 font-medium">
                            {info ? (
                              <>
                                <span className="block">{info.name}</span>
                                <span className="block text-sm font-normal text-black/60">
                                  {challengeDateLabel(info)}
                                </span>
                              </>
                            ) : (
                              `Challenge ${id}`
                            )}
                          </th>
                          <td className="text-green-dark py-3 text-right font-bold">
                            {score} / 3
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              )}
            </section>
          </>
        )}
        <button
          type="button"
          onClick={onHome}
          className="bg-orange focus-visible:outline-green-dark mt-7 rounded-xl px-5 py-3 text-base font-bold text-white transition hover:brightness-95 focus-visible:outline-2 focus-visible:outline-offset-2 active:scale-[0.98]"
        >
          Back to recordings
        </button>
      </main>
    </div>
  )
}
