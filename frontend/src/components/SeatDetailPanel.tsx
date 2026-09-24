import type { Seat } from '../types/analysis'
import { ScoreBar } from './ScoreBar'
import { scoreTextClass } from '../utils/score'

interface Props {
  seat: Seat | null
  onMarkOccupied: (seatId: string, occupied: boolean) => void
  onDelete: (seatId: string) => void
  onAddToComparison: (seatId: string) => void
  onStartMove: (seatId: string) => void
  isMoving: boolean
  busy: boolean
}

export function SeatDetailPanel({
  seat,
  onMarkOccupied,
  onDelete,
  onAddToComparison,
  onStartMove,
  isMoving,
  busy,
}: Props) {
  if (!seat) {
    return (
      <div className="card flex flex-col items-center gap-2 p-8 text-center text-sm text-gray-400">
        <span className="text-2xl" aria-hidden>
          👆
        </span>
        Select a seat on the heatmap to see its estimated exposure score and explanation.
      </div>
    )
  }

  return (
    <div className="card p-6">
      <div className="mb-1 flex items-center justify-between">
        <h3 className="text-lg font-semibold tracking-tight text-gray-900">SEAT {seat.seat_id}</h3>
        <span
          className={`rounded-full px-2 py-0.5 text-xs font-medium ${seat.occupied ? 'bg-orange-100 text-orange-700' : 'bg-emerald-100 text-emerald-700'}`}
        >
          {seat.occupied ? 'Occupied' : 'Empty'}
        </span>
      </div>
      <p className={`mb-4 text-3xl font-semibold tabular-nums ${scoreTextClass(seat.scores.final)}`}>
        {Math.round(seat.scores.final)}
        <span className="ml-1 text-base font-normal text-gray-400">/ 100</span>
      </p>

      <div className="space-y-2.5">
        <ScoreBar label="Distance" value={seat.scores.distance} colorClass="bg-sky-500" />
        <ScoreBar label="Direct Visibility" value={seat.scores.raw_visibility} colorClass="bg-amber-500" />
        <ScoreBar label="Occlusion" value={seat.scores.occlusion} colorClass="bg-rose-500" />
        <ScoreBar label="Angle" value={seat.scores.angle} colorClass="bg-violet-500" />
        <ScoreBar label="Detection Confidence" value={seat.scores.confidence} colorClass="bg-gray-400" />
      </div>

      <div className="mt-5 rounded-xl bg-gray-50/80 p-3">
        <p className="mb-2 text-sm font-medium text-gray-700">Why?</p>
        <ul className="space-y-1.5">
          {seat.explanation.map((reason) => (
            <li key={reason} className="flex gap-2 text-sm text-gray-500">
              <span className="mt-0.5 text-violet-400" aria-hidden>
                •
              </span>
              {reason}
            </li>
          ))}
        </ul>
      </div>

      <p className="mt-4 text-xs text-gray-400">
        Estimated visibility based on the uploaded image and detected classroom geometry — not a
        guarantee of what the instructor can or cannot see.
      </p>

      <div className="mt-5 flex flex-wrap gap-2">
        <button
          disabled={busy}
          onClick={() => onMarkOccupied(seat.seat_id, !seat.occupied)}
          className="rounded-lg border border-gray-200 px-3 py-1.5 text-xs font-medium text-gray-700 transition-colors hover:bg-gray-50 disabled:opacity-50"
        >
          Mark {seat.occupied ? 'Empty' : 'Occupied'}
        </button>
        <button
          disabled={busy}
          onClick={() => onAddToComparison(seat.seat_id)}
          className="rounded-lg border border-gray-200 px-3 py-1.5 text-xs font-medium text-gray-700 transition-colors hover:bg-gray-50 disabled:opacity-50"
        >
          Add to Comparison
        </button>
        <button
          disabled={busy}
          onClick={() => onStartMove(seat.seat_id)}
          className={`rounded-lg border px-3 py-1.5 text-xs font-medium transition-colors disabled:opacity-50
            ${isMoving ? 'border-amber-300 bg-amber-50 text-amber-700' : 'border-gray-200 text-gray-700 hover:bg-gray-50'}`}
        >
          {isMoving ? 'Click the image…' : 'Move This Seat'}
        </button>
        <button
          disabled={busy}
          onClick={() => onDelete(seat.seat_id)}
          className="rounded-lg border border-red-200 px-3 py-1.5 text-xs font-medium text-red-600 transition-colors hover:bg-red-50 disabled:opacity-50"
        >
          Delete Seat
        </button>
      </div>
    </div>
  )
}
