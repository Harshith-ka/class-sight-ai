import type { AnalysisResponse } from '../types/analysis'

interface Props {
  result: AnalysisResponse
}

function Stat({ icon, label, value }: { icon: string; label: string; value: string | number }) {
  return (
    <div className="flex items-start gap-2.5">
      <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-gray-50 text-base" aria-hidden>
        {icon}
      </span>
      <div>
        <p className="text-xs uppercase tracking-wide text-gray-400">{label}</p>
        <p className="text-xl font-semibold tabular-nums text-gray-900">{value}</p>
      </div>
    </div>
  )
}

export function StatsPanel({ result }: Props) {
  const { stats, instructor } = result
  return (
    <div className="card p-6">
      <p className="mb-4 flex items-center gap-2 text-sm font-semibold text-gray-800">
        <span aria-hidden>📊</span> Classroom Analysis
      </p>
      <div className="grid grid-cols-2 gap-x-4 gap-y-5 sm:grid-cols-3">
        <Stat icon="🪑" label="Seats detected" value={stats.seats_detected} />
        <Stat icon="🧑‍🎓" label="Occupied" value={stats.occupied} />
        <Stat icon="⭘" label="Empty" value={stats.empty} />
        <Stat
          icon="🧑‍🏫"
          label="Instructor confidence"
          value={instructor ? `${Math.round(instructor.confidence * 100)}%` : 'N/A'}
        />
        <Stat icon="👁️" label="Avg. visibility" value={`${Math.round(stats.average_visibility)}%`} />
        <Stat icon="🚧" label="Avg. obstruction" value={`${Math.round(stats.average_obstruction)}%`} />
      </div>
    </div>
  )
}
