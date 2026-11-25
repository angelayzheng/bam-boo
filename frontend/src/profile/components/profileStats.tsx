interface ProfileStatsProps {
  totalScore: number
  completedChallenges: number
}

export default function ProfileStats({
  totalScore,
  completedChallenges,
}: ProfileStatsProps) {
  return (
    <dl className="mt-6 grid grid-cols-2 gap-4">
      <div className="bg-green-pale/50 shadow-card rounded-2xl p-5">
        <dt className="text-base text-black/60">Total score</dt>
        <dd className="mt-2 text-4xl font-extrabold">{totalScore}</dd>
      </div>
      <div className="bg-green-pale/50 shadow-card rounded-2xl p-5">
        <dt className="text-base text-black/60">Completed challenges</dt>
        <dd className="mt-2 text-4xl font-extrabold">{completedChallenges}</dd>
      </div>
    </dl>
  )
}
