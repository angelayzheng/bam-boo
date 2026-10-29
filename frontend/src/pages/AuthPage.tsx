import { useEffect, useRef, useState } from 'react'
import type { FormEvent, ReactNode } from 'react'
import Header from '../components/Header'
import { signIn } from '../auth'
import type { AuthUser } from '../auth'

interface AuthPageProps {
  mode: 'login' | 'signup'
  onAuthenticated: (user: AuthUser) => void
  onNavigate: (path: string) => void
  sessionLoading?: boolean
  notice?: ReactNode
}

export default function AuthPage({
  mode,
  onAuthenticated,
  onNavigate,
  sessionLoading = false,
  notice,
}: AuthPageProps) {
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmation, setConfirmation] = useState('')
  const [error, setError] = useState('')
  const [pending, setPending] = useState(false)
  const controller = useRef<AbortController | null>(null)
  const isSignup = mode === 'signup'

  useEffect(() => () => controller.current?.abort(), [])

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (pending || sessionLoading) return
    setError('')
    if (isSignup && password !== confirmation) {
      setError('Your passwords do not match.')
      return
    }
    const request = new AbortController()
    controller.current = request
    setPending(true)
    try {
      const user = await signIn(
        mode,
        {
          username: username.trim(),
          password,
          ...(isSignup ? { email: email.trim() } : {}),
        },
        request.signal,
      )
      if (!request.signal.aborted) onAuthenticated(user)
    } catch (cause) {
      if (!request.signal.aborted)
        setError(
          cause instanceof Error
            ? cause.message
            : 'Could not sign in. Please try again.',
        )
    } finally {
      if (!request.signal.aborted) setPending(false)
    }
  }

  const inputClass =
    'mt-2 w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-[#17243d] outline-none focus:border-[#19856a] focus:ring-2 focus:ring-[#19856a]/20'

  return (
    <div className="min-h-screen bg-[#f7f8f5] text-[#17243d]">
      <Header compact onHome={() => onNavigate('/')} />
      <main className="mx-auto max-w-md px-5 py-12 sm:py-16">
        {notice}
        <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
          <p className="text-xs font-bold tracking-widest text-[#19856a] uppercase">
            Your bam-boo account
          </p>
          <h1 className="mt-3 text-3xl font-bold tracking-tight">
            {isSignup ? 'Create an account' : 'Welcome back'}
          </h1>
          <p className="mt-3 text-sm text-slate-600">
            {isSignup
              ? 'Make yourself at home and view your training profile.'
              : 'Log in to view your profile and progress.'}
          </p>
          <form
            onSubmit={submit}
            className="mt-7 space-y-5"
            aria-busy={pending}
          >
            <label className="block text-sm font-semibold" htmlFor="username">
              Username
              <input
                className={inputClass}
                id="username"
                name="username"
                autoComplete="username"
                required
                maxLength={150}
                value={username}
                onChange={(event) => setUsername(event.target.value)}
                disabled={pending}
              />
            </label>
            {isSignup && (
              <label className="block text-sm font-semibold" htmlFor="email">
                Email{' '}
                <span className="font-normal text-slate-500">(optional)</span>
                <input
                  className={inputClass}
                  id="email"
                  name="email"
                  type="email"
                  autoComplete="email"
                  maxLength={254}
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  disabled={pending}
                />
              </label>
            )}
            <label className="block text-sm font-semibold" htmlFor="password">
              Password
              <input
                className={inputClass}
                id="password"
                name="password"
                type="password"
                autoComplete={isSignup ? 'new-password' : 'current-password'}
                required
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                disabled={pending}
                aria-describedby={isSignup ? 'password-hint' : undefined}
              />
            </label>
            {isSignup && (
              <>
                <p
                  id="password-hint"
                  className="text-xs leading-relaxed text-slate-500"
                >
                  Use at least 8 characters. Avoid common passwords, only
                  numbers, or a password similar to your username or email.
                </p>
                <label
                  className="block text-sm font-semibold"
                  htmlFor="confirmation"
                >
                  Confirm password
                  <input
                    className={inputClass}
                    id="confirmation"
                    name="confirmation"
                    type="password"
                    autoComplete="new-password"
                    required
                    value={confirmation}
                    onChange={(event) => setConfirmation(event.target.value)}
                    disabled={pending}
                  />
                </label>
              </>
            )}
            {error && (
              <p
                role="alert"
                className="rounded-xl bg-red-50 p-3 text-sm text-red-800"
              >
                {error}
              </p>
            )}
            <button
              type="submit"
              disabled={pending || sessionLoading}
              className="w-full rounded-xl bg-[#17243d] px-5 py-3 font-semibold text-white hover:bg-[#223253] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#19856a] disabled:cursor-wait disabled:opacity-60"
            >
              {sessionLoading
                ? 'Checking account…'
                : pending
                  ? 'Please wait…'
                  : isSignup
                    ? 'Create account'
                    : 'Log in'}
            </button>
          </form>
          <p className="mt-6 text-center text-sm text-slate-600">
            {isSignup ? 'Already have an account? ' : 'New here? '}
            <a
              href={isSignup ? '/login' : '/signup'}
              onClick={(event) => {
                event.preventDefault()
                onNavigate(isSignup ? '/login' : '/signup')
              }}
              className="font-semibold text-[#176d59] underline underline-offset-4"
            >
              {isSignup ? 'Log in' : 'Create an account'}
            </a>
          </p>
        </div>
        <a
          href="/"
          onClick={(event) => {
            event.preventDefault()
            onNavigate('/')
          }}
          className="mt-6 block text-center text-sm font-semibold text-slate-600 underline underline-offset-4"
        >
          Continue to recordings
        </a>
      </main>
    </div>
  )
}
