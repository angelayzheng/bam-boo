const WEEKDAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']

export default function WeekdayStrip() {
  return (
    <section className="grid grid-cols-5 gap-2 sm:gap-4">
      {WEEKDAYS.map((day) => (
        <div key={day} className="flex flex-col items-center gap-3">
          <span className="text-xl font-extrabold uppercase sm:text-3xl">
            {day}
          </span>
          <div className="bg-green-pale shadow-card aspect-square w-full rounded-full" />
        </div>
      ))}
    </section>
  )
}
