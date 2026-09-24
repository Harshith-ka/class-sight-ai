import type { Seat } from '../types/analysis'
import { ScoreBar } from './ScoreBar'
import { scoreTextClass } from '../utils/score'

interface Props {
  seats: Seat[]
  onClear: () => void
}

export function ComparisonPanel({ seats, onClear }: Props) {
  if (seats.length < 2) {
    return (
      <div className="card flex flex-col items-center gap-2 p-8 text-center text-sm text-gray-400">
        <span className="text-2xl" aria-hidden>
          ⚖️
        </span>
        Select two seats (use "Add to Comparison" in the seat detail panel) to compare them
        side-by-side.
      </div>
    )
  }

  const [a, b] = seats
  const rows: [string, keyof Seat['scores']][] = [
    ['Distance', 'distance'],
    ['Visibility', 'raw_visibility'],
    ['Occlusion', 'occlusion'],
    ['Angle', 'angle'],
  ]

  return (
    <div className="card p-6">
      <div className="mb-4 flex items-center justify-between">
        <p className="flex items-center gap-2 text-sm font-semibold text-gray-800">
          <span aria-hidden>⚖️</span> {a.seat_id} vs {b.seat_id}
        </p>
        <button onClick={onClear} className="text-xs text-gray-400 transition-colors hover:text-gray-600">
          Clear
        </button>
      </div>

      <div className="mb-4 grid grid-cols-2 gap-4 text-center">
        {[a, b].map((seat) => (
          <div key={seat.seat_id}>
            <p className={`text-2xl font-semibold tabular-nums ${scoreTextClass(seat.scores.final)}`}>
              {Math.round(seat.scores.final)}
            </p>
            <p className="text-xs text-gray-400">{seat.seat_id}</p>
          </div>
        ))}
      </div>

      <div className="space-y-4">
        {rows.map(([label, key]) => (
          <div key={label}>
            <p className="mb-1 text-xs font-medium text-gray-500">{label}</p>
            <div className="grid grid-cols-2 gap-3">
              <ScoreBar label={a.seat_id} value={a.scores[key] as number} />
              <ScoreBar label={b.seat_id} value={b.scores[key] as number} />
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
