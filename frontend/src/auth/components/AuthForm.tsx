import type { FormEvent } from 'react'
import type { SignupGroup } from '../boundaries/dataAccessInterfaces'

type GroupsStatus = 'loading' | 'ready' | 'error'

export interface AuthFlow {
  username: string
  email: string
  groupId: string
  password: string
  confirmation: string
  error: string
  pending: boolean
  groups: SignupGroup[]
  groupsStatus: GroupsStatus
  groupsError: string
  setUsername: (value: string) => void
  setEmail: (value: string) => void
  setGroupId: (value: string) => void
  setPassword: (value: string) => void
  setConfirmation: (value: string) => void
  submit: (event: FormEvent<HTMLFormElement>) => Promise<void>
  retryGroups: () => void
}

interface AuthFormProps {
  mode: 'login' | 'signup'
  sessionLoading: boolean
  flow: AuthFlow
}

const inputClass =
  'mt-2 w-full rounded-xl border-1 border-green-light bg-white px-4 py-3 text-black outline-none placeholder:text-black/30 focus:border-green-dark focus:ring-4 focus:ring-green-dark/10 disabled:opacity-60'

export default function AuthForm({
  mode,
  sessionLoading,
  flow,
}: AuthFormProps) {
  const isSignup = mode === 'signup'

  return (
    <form
      onSubmit={flow.submit}
      className="mt-7 space-y-5"
      aria-busy={flow.pending}
    >
      <label className="block text-base font-semibold" htmlFor="username">
        Username
        <input
          className={inputClass}
          id="username"
          name="username"
          autoComplete="username"
          required
          maxLength={150}
          value={flow.username}
          onChange={(event) => flow.setUsername(event.target.value)}
          disabled={flow.pending}
        />
      </label>
      {isSignup && (
        <label className="block text-base font-semibold" htmlFor="email">
          Email <span className="font-normal text-black/50">(optional)</span>
          <input
            className={inputClass}
            id="email"
            name="email"
            type="email"
            autoComplete="email"
            maxLength={254}
            value={flow.email}
            onChange={(event) => flow.setEmail(event.target.value)}
            disabled={flow.pending}
          />
        </label>
      )}
      {isSignup && (
        <div>
          <label className="block text-base font-semibold" htmlFor="group">
            Group <span className="font-normal text-black/50">(optional)</span>
            <select
              id="group"
              name="group_id"
              className={inputClass}
              value={flow.groupId}
              onChange={(event) => flow.setGroupId(event.target.value)}
              disabled={flow.pending || flow.groupsStatus === 'loading'}
              aria-describedby="group-status"
            >
              <option value="">No group</option>
              {flow.groups.map((choice) => (
                <option key={choice.id} value={choice.id}>
                  {choice.name}
                </option>
              ))}
            </select>
          </label>
          <div id="group-status" className="mt-2 text-sm text-black/60">
            {flow.groupsStatus === 'loading' ? (
              <p role="status">Loading groups…</p>
            ) : flow.groupsStatus === 'error' ? (
              <p role="alert">
                {flow.groupsError}{' '}
                <button
                  type="button"
                  disabled={flow.pending}
                  onClick={flow.retryGroups}
                  className="text-green-dark font-semibold underline underline-offset-4 transition hover:text-black"
                >
                  Retry
                </button>
              </p>
            ) : flow.groups.length === 0 ? (
              <p>No groups are available yet.</p>
            ) : null}
          </div>
        </div>
      )}
      <label className="block text-base font-semibold" htmlFor="password">
        Password
        <input
          className={inputClass}
          id="password"
          name="password"
          type="password"
          autoComplete={isSignup ? 'new-password' : 'current-password'}
          required
          value={flow.password}
          onChange={(event) => flow.setPassword(event.target.value)}
          disabled={flow.pending}
          aria-describedby={isSignup ? 'password-hint' : undefined}
        />
      </label>
      {isSignup && (
        <>
          <p
            id="password-hint"
            className="text-sm leading-relaxed text-black/60"
          >
            Use at least 8 characters. Avoid common passwords, only numbers, or
            a password similar to your username or email.
          </p>
          <label
            className="block text-base font-semibold"
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
              value={flow.confirmation}
              onChange={(event) => flow.setConfirmation(event.target.value)}
              disabled={flow.pending}
            />
          </label>
        </>
      )}
      {flow.error && (
        <p
          role="alert"
          className="rounded-xl bg-red-50 p-3 text-base text-red-800"
        >
          {flow.error}
        </p>
      )}
      <button
        type="submit"
        disabled={flow.pending || sessionLoading}
        className="bg-orange focus-visible:outline-green-dark w-full rounded-xl px-5 py-3 text-base font-bold text-white transition hover:brightness-95 focus-visible:outline-2 focus-visible:outline-offset-2 active:scale-[0.98] disabled:cursor-wait disabled:opacity-60"
      >
        {sessionLoading
          ? 'Checking account…'
          : flow.pending
            ? 'Please wait…'
            : isSignup
              ? 'Create account'
              : 'Log in'}
      </button>
    </form>
  )
}
