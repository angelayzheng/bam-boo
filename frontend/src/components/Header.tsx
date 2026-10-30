import { FlameIcon } from './icons'
import logo from '../assets/bamboo-logo-inline.svg'

interface HeaderProps {
  compact?: boolean
}

export default function Header({ compact = false }: HeaderProps) {
  return (
    <header className="bg-beige">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-5 py-4 sm:px-8">
        <div className="flex items-center gap-8">
          <img src={logo} alt="Bam-boo!" className="h-9 w-auto" />
          {!compact && (
            <nav className="hidden items-center gap-6 text-lg font-bold text-black sm:flex">
              <a href="/">Today’s Challenge</a>
              <a href="/leaderboard">Leaderboard</a>
            </nav>
          )}
        </div>
        {!compact && (
          <div className="flex items-center gap-4 sm:gap-5">
            <div className="text-orange flex items-center gap-1 text-lg font-bold">
              <FlameIcon className="size-5" />
              <span>3</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="bg-green-light grid size-8 place-items-center rounded-full text-xs font-bold text-black">
                AZ
              </div>
              <span className="hidden text-lg font-bold text-black sm:inline">
                Angela Zheng
              </span>
            </div>
          </div>
        )}
      </div>
    </header>
  )
}
