interface ProfileHeaderProps {
  loggingOut: boolean
  logoutError: string
  onLogout: () => void
}

export default function ProfileHeader({
  loggingOut,
  logoutError,
  onLogout,
}: ProfileHeaderProps) {
  return (
    <>
      <div className="mb-7 flex flex-wrap items-center justify-between gap-4">
        <h1 className="text-orange text-4xl font-extrabold">My Profile</h1>
        <button
          type="button"
          onClick={onLogout}
          disabled={loggingOut}
          className="border-green-dark text-green-dark hover:bg-green-pale/50 focus-visible:outline-green-dark rounded-xl border-2 px-5 py-3 text-base font-bold transition focus-visible:outline-2 focus-visible:outline-offset-2 disabled:opacity-60"
        >
          {loggingOut ? 'Logging out…' : 'Log out'}
        </button>
      </div>
      {logoutError && (
        <p
          role="alert"
          className="mb-5 rounded-xl bg-red-50 p-4 text-base text-red-800"
        >
          {logoutError}
        </p>
      )}
    </>
  )
}
