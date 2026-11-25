interface AccountDetailsProps {
  username: string
  email: string
  avatarEmoji: string
}

export default function AccountDetails({
  username,
  email,
  avatarEmoji,
}: AccountDetailsProps) {
  return (
    <section
      aria-label="Account details"
      className="shadow-card flex items-center gap-5 rounded-2xl bg-white/60 p-6"
    >
      <span
        role="img"
        aria-label="Account avatar"
        className="bg-green-pale grid size-20 shrink-0 place-items-center rounded-2xl text-4xl"
      >
        {avatarEmoji}
      </span>
      <div className="min-w-0">
        <h2 className="text-2xl font-bold break-words">{username}</h2>
        <p className="mt-1 text-base break-words text-black/60">
          {email || 'No email provided'}
        </p>
      </div>
    </section>
  )
}
