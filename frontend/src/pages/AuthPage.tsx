import type { ReactNode } from 'react'
import Header from '../components/Header'
import type { AuthUser } from '../entities/types'
import AuthForm from '../auth/components/AuthForm'
import { useAuthFlow } from './useAuthFlow'

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
  const isSignup = mode === 'signup'
  const flow = useAuthFlow({ mode, sessionLoading, onAuthenticated })

  return (
    <div className="bg-beige min-h-screen text-black">
      <Header compact onHome={() => onNavigate('/')} />
      <main className="mx-auto max-w-md px-5 py-12 sm:py-16">
        {notice}
        <div className="shadow-card rounded-2xl bg-white/60 p-6 sm:p-8">
          <p className="text-green-dark text-sm font-bold tracking-widest uppercase">
            Your bam-boo account
          </p>
          <h1 className="text-orange mt-3 text-4xl font-extrabold">
            {isSignup ? 'Create an account' : 'Welcome back'}
          </h1>
          <p className="mt-3 text-base text-black/70">
            {isSignup
              ? 'Make yourself at home and view your training profile.'
              : 'Log in to view your profile and progress.'}
          </p>
          <AuthForm mode={mode} sessionLoading={sessionLoading} flow={flow} />
          <p className="mt-6 text-center text-base text-black/70">
            {isSignup ? 'Already have an account? ' : 'New here? '}
            <a
              href={isSignup ? '/login' : '/signup'}
              onClick={(event) => {
                event.preventDefault()
                onNavigate(isSignup ? '/login' : '/signup')
              }}
              className="text-green-dark font-semibold underline underline-offset-4 transition hover:text-black"
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
          className="mt-6 block text-center text-base font-semibold text-black/70 underline underline-offset-4 transition hover:text-black"
        >
          Continue to recordings
        </a>
      </main>
    </div>
  )
}
