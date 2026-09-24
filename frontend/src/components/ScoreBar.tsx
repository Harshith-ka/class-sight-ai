interface Props {
  label: string
  value: number
  colorClass?: string
}

export function ScoreBar({ label, value, colorClass = 'bg-violet-500' }: Props) {
  const clamped = Math.min(100, Math.max(0, value))
  return (
    <div className="flex items-center gap-3 text-sm">
      <span className="w-28 shrink-0 truncate text-gray-500">{label}</span>
      <div className="h-2 flex-1 overflow-hidden rounded-full bg-gray-100">
        <div
          className={`h-full rounded-full transition-all duration-500 ease-out ${colorClass}`}
          style={{ width: `${clamped}%` }}
        />
      </div>
      <span className="w-8 shrink-0 text-right font-medium tabular-nums text-gray-700">
        {Math.round(clamped)}
      </span>
    </div>
  )
}
