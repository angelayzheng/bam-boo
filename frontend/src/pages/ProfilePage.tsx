import type { ReactNode } from 'react'
import Header from '../components/Header'
import type { AuthUser, ChallengeSummary } from '../entities/types'
import AccountDetails from '../profile/components/AccountDetails'
import ProfileHeader from '../profile/components/ProfileHeader'
import ProfileProgress from '../profile/components/ProfileProgress'
import { useProfileFlow } from './useProfileFlow'

interface ProfilePageProps {
  user: AuthUser
  summaries: ChallengeSummary[]
  onLoggedOut: () => void
  onHome: () => void
  onChallenge?: () => void
  notice?: ReactNode
  progressVersion?: number
}

export default function ProfilePage({
  user,
  summaries,
  onLoggedOut,
  onHome,
  onChallenge,
  notice,
  progressVersion = 0,
}: ProfilePageProps) {
  const { viewModel, retry, logout, loggingOut, logoutError } = useProfileFlow({
    user,
    summaries,
    progressVersion,
    onLoggedOut,
  })

  return (
    <div className="bg-beige min-h-screen text-black">
      <Header user={user} onHome={onHome} onChallenge={onChallenge} />
      <main className="mx-auto max-w-3xl px-5 py-10 sm:py-14">
        {notice}
        <ProfileHeader
          loggingOut={loggingOut}
          logoutError={logoutError}
          onLogout={logout}
        />
        <AccountDetails
          username={viewModel.username}
          email={viewModel.email}
          avatarEmoji={viewModel.avatarEmoji}
        />
        <ProfileProgress viewModel={viewModel} onRetry={retry} />
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
