export default function Stars({ value }: { value: number }) {
  return (
    <span
      className="text-green-light flex text-[10px] leading-none sm:text-lg"
      role="img"
      aria-label={`${value} out of 3 stars`}
    >
      {[0, 1, 2].map((index) => {
        const fill = Math.min(1, Math.max(0, value - index))
        return (
          <span key={index} className="relative inline-block">
            <span>☆</span>
            <span
              className="absolute inset-0 overflow-hidden"
              style={{ width: `${fill * 100}%` }}
            >
              ★
            </span>
          </span>
        )
      })}
    </span>
  )
}
