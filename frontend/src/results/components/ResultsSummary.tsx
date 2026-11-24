import { CheckIcon, StarIcon } from '../../components/icons'

interface ResultsSummaryProps {
  heading: string
  challengeName: string
  dateLabel: string
  starCount: number
  stars: boolean[]
}

export default function ResultsSummary({
  heading,
  challengeName,
  dateLabel,
  starCount,
  stars,
}: ResultsSummaryProps) {
  return (
    <>
      <div className="bg-green-dark shadow-card grid size-16 place-items-center rounded-3xl text-white">
        <CheckIcon className="size-8" />
      </div>
      <p className="text-green-dark mt-7 text-sm font-bold tracking-[0.18em] uppercase">
        Challenge complete
      </p>
      <h1 className="text-orange mt-3 text-4xl font-extrabold sm:text-5xl">
        {heading}
      </h1>
      <p className="mt-4 max-w-lg text-lg leading-7 text-black/70">
        “{challengeName}” · {dateLabel}
      </p>

      <div
        className="my-9 flex gap-3"
        aria-label={`${starCount} out of 3 stars earned`}
      >
        {stars.map((earned, index) => (
          <StarIcon
            key={index}
            className={`size-13 drop-shadow-md sm:size-16 ${earned ? 'text-green-light' : 'text-green-pale'}`}
          />
        ))}
      </div>
    </>
  )
}
