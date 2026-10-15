interface IconProps {
  className?: string
}

export function ArrowLeftIcon({ className = 'size-5' }: IconProps) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true">
      <path d="m15 18-6-6 6-6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

export function CheckIcon({ className = 'size-5' }: IconProps) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
      <path d="m5 12 4 4L19 6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

export function HeadphonesIcon({ className = 'size-5' }: IconProps) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true">
      <path d="M4 14v-2a8 8 0 0 1 16 0v2" />
      <path d="M4 14h3v6H5a1 1 0 0 1-1-1v-5Zm16 0h-3v6h2a1 1 0 0 0 1-1v-5Z" />
    </svg>
  )
}

export function FlameIcon({ className = 'size-5' }: IconProps) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <path d="M13.6 2.3c.4 3-1.5 4.7-3.1 6.2C9 9.9 7.7 11 8.2 13.2c.2.8.7 1.5 1.4 2-.1-1.7.8-2.8 2.4-4.1-.1 1.8 1.1 2.7 2 3.7.7.7 1.1 1.6.9 2.7 1.5-.8 2.6-2.4 2.8-4.2.4-4-2.2-7.5-4.1-11Z" />
      <path d="M7.1 9.6C5 11.5 4 13.6 4.3 16.1A7.7 7.7 0 0 0 12 23a7.7 7.7 0 0 0 7.7-6.9c.2-1.7-.2-3.4-1.1-4.9.1.7.1 1.4 0 2.2-.3 2.7-2.2 5-4.7 5.9-1.2.4-2.5.5-3.7.1a5.3 5.3 0 0 1-3.8-4.2c-.3-1.9.2-3.7.7-5.6Z" opacity=".35" />
    </svg>
  )
}

export function StarIcon({ className = 'size-5' }: IconProps) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <path d="m12 2.5 2.9 5.9 6.5.9-4.7 4.6 1.1 6.5-5.8-3.1-5.8 3.1 1.1-6.5-4.7-4.6 6.5-.9L12 2.5Z" />
    </svg>
  )
}

export function PlayIcon({ className = 'size-5' }: IconProps) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <path d="M8.4 5.6a1 1 0 0 1 1.5-.8l8.6 6.4a1 1 0 0 1 0 1.6l-8.6 6.4a1 1 0 0 1-1.5-.8V5.6Z" />
    </svg>
  )
}

export function PauseIcon({ className = 'size-5' }: IconProps) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <rect x="6" y="5" width="4" height="14" rx="1" />
      <rect x="14" y="5" width="4" height="14" rx="1" />
    </svg>
  )
}
