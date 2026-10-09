import { FlameIcon, HeadphonesIcon } from './icons'

interface HeaderProps {
  compact?: boolean
}

export default function Header({ compact = false }: HeaderProps) {
  return (
    <header className="border-b border-slate-200/80 bg-white/85 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-5 py-4 sm:px-8">
        <div className="flex items-center gap-3">
          <div className="grid size-10 place-items-center rounded-xl bg-[#17243d] text-[#75e2c1]">
            <HeadphonesIcon />
          </div>
          <p className="text-[11px] leading-none font-bold tracking-[0.18em] text-[#19856a] uppercase">
            bam-<em>boo</em>!
          </p>
        </div>
        {!compact && (
          <div className="flex items-center gap-2 sm:gap-5">
            <div className="hidden items-center gap-2 text-sm font-semibold text-slate-700 sm:flex">
              <FlameIcon className="size-5 text-[#ff8a4c]" />
              <span>7 day streak</span>
            </div>
            <div className="grid size-9 place-items-center rounded-full bg-[#d9f7ed] text-sm font-bold text-[#176d59] ring-2 ring-white">AM</div>
          </div>
        )}
      </div>
    </header>
  )
}
