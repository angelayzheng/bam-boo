import { useEffect, useState } from 'react'
import type { ReactNode } from 'react'
import Header from '../components/Header'
import { loadProfile } from '../auth'
import type { AuthUser, UserProfile } from '../auth'

interface ProfilePageProps {
  user: AuthUser
  onLogout: () => Promise<void>
  onHome: () => void
  notice?: ReactNode
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
}: ProfilePageProps) {
  const [profile, setProfile] = useState<UserProfile | null>(null)
  const [error, setError] = useState('')
  const [attempt, setAttempt] = useState(0)
  const [loggingOut, setLoggingOut] = useState(false)
  const [logoutError, setLogoutError] = useState('')

  useEffect(() => {
    const controller = new AbortController()
    loadProfile(user.id, controller.signal)
      .then((loaded) => {
        if (!controller.signal.aborted) setProfile(loaded)
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
  }, [user.id, attempt])

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
    <div className="min-h-screen bg-[#f7f8f5] text-[#17243d]">
      <Header user={user} onHome={onHome} />
      <main className="mx-auto max-w-3xl px-5 py-10 sm:py-14">
        {notice}
        <div className="mb-7 flex flex-wrap items-center justify-between gap-4">
          <h1 className="text-3xl font-bold tracking-tight">My profile</h1>
          <button
            type="button"
            onClick={logout}
            disabled={loggingOut}
            className="rounded-xl border border-slate-300 bg-white px-5 py-3 text-sm font-semibold hover:bg-slate-50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#19856a] disabled:opacity-60"
          >
            {loggingOut ? 'Logging out…' : 'Log out'}
          </button>
        </div>
        {logoutError && (
          <p
            role="alert"
            className="mb-5 rounded-xl bg-red-50 p-4 text-sm text-red-800"
          >
            {logoutError}
          </p>
        )}
        <section
          aria-label="Account details"
          className="flex items-center gap-5 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm"
        >
          <span
            role="img"
            aria-label={profile ? `${profile.avatar} avatar` : 'Account avatar'}
            className="grid size-20 shrink-0 place-items-center rounded-2xl bg-[#d9f7ed] text-4xl"
          >
            {profile ? (avatars[profile.avatar] ?? '👤') : '👤'}
          </span>
          <div className="min-w-0">
            <h2 className="text-xl font-bold break-words">{user.username}</h2>
            <p className="mt-1 text-sm break-words text-slate-500">
              {user.email || 'No email provided'}
            </p>
          </div>
        </section>
        {error ? (
          <div className="mt-6 rounded-2xl border border-red-200 bg-white p-5">
            <p role="alert" className="text-sm text-red-800">
              {error}
            </p>
            <button
              type="button"
              onClick={() => {
                setError('')
                setAttempt((value) => value + 1)
              }}
              className="mt-3 font-semibold text-[#176d59] underline underline-offset-4"
            >
              Try again
            </button>
          </div>
        ) : !profile ? (
          <p role="status" className="mt-6 text-slate-500">
            Loading your progress…
          </p>
        ) : (
          <>
            <dl className="mt-6 grid grid-cols-2 gap-4">
              <div className="rounded-2xl border border-slate-200 bg-white p-5">
                <dt className="text-sm text-slate-500">Total score</dt>
                <dd className="mt-2 text-3xl font-bold">
                  {profile.total_score}
                </dd>
              </div>
              <div className="rounded-2xl border border-slate-200 bg-white p-5">
                <dt className="text-sm text-slate-500">Completed challenges</dt>
                <dd className="mt-2 text-3xl font-bold">
                  {profile.completed_challenges}
                </dd>
              </div>
            </dl>
            <section className="mt-6 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
              <h2 className="text-lg font-bold">Challenge scores</h2>
              {Object.keys(profile.scores).length === 0 ? (
                <p className="mt-3 text-sm leading-relaxed text-slate-500">
                  No saved scores yet. Challenge results currently stay in this
                  browser session and are not saved to your account.
                </p>
              ) : (
                <table className="mt-4 w-full text-left text-sm">
                  <thead>
                    <tr className="border-b border-slate-200 text-slate-500">
                      <th scope="col" className="py-3 font-medium">
                        Challenge
                      </th>
                      <th scope="col" className="py-3 text-right font-medium">
                        Score
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(profile.scores).map(([id, score]) => (
                      <tr
                        key={id}
                        className="border-b border-slate-100 last:border-0"
                      >
                        <th scope="row" className="py-3 font-medium break-all">
                          {id}
                        </th>
                        <td className="py-3 text-right">{score} / 100</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </section>
          </>
        )}
        <button
          type="button"
          onClick={onHome}
          className="mt-7 rounded-xl bg-[#17243d] px-5 py-3 font-semibold text-white hover:bg-[#223253] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#19856a]"
        >
          Back to recordings
        </button>
      </main>
    </div>
  )
}
