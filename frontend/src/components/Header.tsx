import { HeadphonesIcon } from './icons'
import type { AuthUser } from '../auth'

interface HeaderProps {
  compact?: boolean
  user?: AuthUser | null
  accountLoading?: boolean
  onAccount?: () => void
  onHome?: () => void
}

export default function Header({
  compact = false,
  user,
  accountLoading = false,
  onAccount,
  onHome,
}: HeaderProps) {
  return (
    <header className="border-b border-slate-200/80 bg-white/85 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-5 py-4 sm:px-8">
        <a
          href="/"
          onClick={
            onHome
              ? (event) => {
                  event.preventDefault()
                  onHome()
                }
              : undefined
          }
          className="flex items-center gap-3 rounded-lg focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-[#19856a]"
          aria-label="bam-boo home"
        >
          <div className="grid size-10 place-items-center rounded-xl bg-[#17243d] text-[#75e2c1]">
            <HeadphonesIcon />
          </div>
          <p className="text-[11px] leading-none font-bold tracking-[0.18em] text-[#19856a] uppercase">
            bam-<em>boo</em>!
          </p>
        </a>
        {!compact &&
          (accountLoading ? (
            <span role="status" className="text-sm text-slate-500">
              Checking account…
            </span>
          ) : (
            <a
              href={user ? '/profile' : '/login'}
              onClick={
                onAccount
                  ? (event) => {
                      event.preventDefault()
                      onAccount()
                    }
                  : undefined
              }
              className="flex min-w-0 items-center gap-2 rounded-xl px-3 py-2 text-sm font-semibold text-[#176d59] hover:bg-[#d9f7ed] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#19856a]"
            >
              {user && (
                <span
                  aria-hidden="true"
                  className="grid size-9 shrink-0 place-items-center rounded-full bg-[#d9f7ed] font-bold"
                >
                  {user.username.slice(0, 2).toUpperCase()}
                </span>
              )}
              <span className="max-w-36 truncate">
                {user ? 'My profile' : 'Log in'}
              </span>
            </a>
          ))}
      </div>
    </header>
  )
}
