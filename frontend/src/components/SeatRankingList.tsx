import type { Seat } from '../types/analysis'
import { scoreSoftBgClass } from '../utils/score'

interface Props {
  seats: Seat[]
  selectedSeatId: string | null
  onSelectSeat: (seatId: string) => void
}

const RANK_MEDALS = ['🥇', '🥈', '🥉']

export function SeatRankingList({ seats, selectedSeatId, onSelectSeat }: Props) {
  const ranked = [...seats].sort((a, b) => b.scores.final - a.scores.final).slice(0, 5)

  return (
    <div className="card p-5">
      <p className="mb-3 flex items-center gap-2 text-sm font-semibold text-gray-800">
        <span aria-hidden>🏆</span> Top 5 Low-Exposure Seats
      </p>
      <ol className="space-y-1.5">
        {ranked.map((seat, i) => (
          <li key={seat.seat_id}>
            <button
              onClick={() => onSelectSeat(seat.seat_id)}
              className={`flex w-full items-center justify-between rounded-lg px-3 py-2 text-sm transition-colors
                ${selectedSeatId === seat.seat_id ? 'bg-violet-50 text-violet-700' : 'text-gray-700 hover:bg-gray-50'}`}
            >
              <span className="flex items-center gap-2">
                <span className="w-5 text-center" aria-hidden>
                  {RANK_MEDALS[i] ?? i + 1}
                </span>
                {seat.seat_id}
              </span>
              <span
                className={`rounded-full px-2 py-0.5 text-xs font-semibold tabular-nums ${scoreSoftBgClass(seat.scores.final)}`}
              >
                {Math.round(seat.scores.final)}
              </span>
            </button>
          </li>
        ))}
        {ranked.length === 0 && <p className="text-sm text-gray-400">No seats detected.</p>}
      </ol>
    </div>
  )
}
