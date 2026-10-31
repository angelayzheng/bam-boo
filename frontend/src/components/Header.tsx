import type { MouseEvent } from 'react'
import { FlameIcon } from './icons'
import logo from '../assets/bamboo-logo-inline.svg'
import type { AuthUser } from '../auth'

interface HeaderProps {
  compact?: boolean
  user?: AuthUser | null
  accountLoading?: boolean
  onAccount?: () => void
  onHome?: () => void
  onChallenge?: () => void
}

// Runs a navigation callback without a full page reload, if one is provided.
function navigate(callback?: () => void) {
  return callback
    ? (event: MouseEvent) => {
        event.preventDefault()
        callback()
      }
    : undefined
}

const navLink =
  'rounded-lg px-2 py-1 transition hover:bg-green-pale/60 hover:text-green-dark focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-green-dark'

export default function Header({
  compact = false,
  user,
  accountLoading = false,
  onAccount,
  onHome,
  onChallenge,
}: HeaderProps) {
  return (
    <header className="bg-beige">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-5 py-4 sm:px-8">
        <div className="flex items-center gap-8">
          <a
            href="/"
            onClick={navigate(onHome)}
            className="focus-visible:outline-green-dark rounded-lg transition hover:opacity-80 focus-visible:outline-2 focus-visible:outline-offset-4"
            aria-label="bam-boo home"
          >
            <img src={logo} alt="Bam-boo!" className="h-9 w-auto" />
          </a>
          {!compact && (
            <nav className="hidden items-center gap-4 text-lg font-bold text-black sm:flex">
              <a
                href="/"
                onClick={navigate(onChallenge ?? onHome)}
                className={navLink}
              >
                Today’s Challenge
              </a>
              <a href="/leaderboard" className={navLink}>
                Leaderboard
              </a>
            </nav>
          )}
        </div>
        {!compact &&
          (accountLoading ? (
            <span role="status" className="text-base text-black/60">
              Checking account…
            </span>
          ) : (
            <div className="flex items-center gap-4 sm:gap-5">
              {user && (
                // TODO: replace with the user's real streak once available.
                <div className="text-orange flex items-center gap-1 text-lg font-bold">
                  <FlameIcon className="size-5" />
                  <span>3</span>
                </div>
              )}
              <a
                href={user ? '/profile' : '/login'}
                onClick={navigate(onAccount)}
                className="focus-visible:outline-green-dark hover:bg-green-pale/50 flex min-w-0 items-center gap-2 rounded-xl px-2 py-1 text-lg font-bold text-black transition focus-visible:outline-2 focus-visible:outline-offset-2"
              >
                {user && (
                  <span
                    aria-hidden="true"
                    className="bg-green-light grid size-8 shrink-0 place-items-center rounded-full text-xs font-bold text-black"
                  >
                    {user.username.slice(0, 2).toUpperCase()}
                  </span>
                )}
                <span className="max-w-36 truncate">
                  {user ? user.username : 'Log in'}
                </span>
              </a>
            </div>
          ))}
      </div>
    </header>
  )
}