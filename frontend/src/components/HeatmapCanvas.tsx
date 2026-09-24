import { useRef } from 'react'
import type { AnalysisResponse, CorrectionMode } from '../types/analysis'

interface Props {
  result: AnalysisResponse
  selectedSeatId: string | null
  comparisonSeatIds: string[]
  correctionMode: CorrectionMode
  /** Seat currently being repositioned via "Move This Seat"; takes priority
   * over `correctionMode` for click handling and cursor/banner state. */
  movingSeatId: string | null
  onSelectSeat: (seatId: string) => void
  onCanvasClick: (xNorm: number, yNorm: number) => void
}

const LEGEND: [string, string][] = [
  ['bg-emerald-500', 'Low exposure'],
  ['bg-amber-500', 'Medium'],
  ['bg-orange-500', 'Elevated'],
  ['bg-rose-500', 'High'],
]

export function HeatmapCanvas({
  result,
  selectedSeatId,
  comparisonSeatIds,
  correctionMode,
  movingSeatId,
  onSelectSeat,
  onCanvasClick,
}: Props) {
  const wrapperRef = useRef<HTMLDivElement>(null)
  const active = movingSeatId ? 'move-seat' : correctionMode

  const handleWrapperClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (active === 'none' || !wrapperRef.current) return
    const rect = wrapperRef.current.getBoundingClientRect()
    const x = (e.clientX - rect.left) / rect.width
    const y = (e.clientY - rect.top) / rect.height
    onCanvasClick(Math.min(1, Math.max(0, x)), Math.min(1, Math.max(0, y)))
  }

  const cursorClass = active === 'none' ? 'cursor-default' : active === 'add-seat' ? 'cursor-copy' : 'cursor-crosshair'

  const banner: Record<string, string> = {
    'move-instructor': 'Click on the image to set the instructor position.',
    'move-board': 'Click on the image to mark the board — improves angle accuracy for every seat.',
    'add-seat': 'Click on the image to add a seat at that position.',
    'move-seat': `Click on the image to move seat ${movingSeatId} there.`,
  }

  return (
    <div className="card overflow-hidden p-3">
      <div className="mb-2 flex flex-wrap items-center justify-between gap-2 px-1">
        <p className="flex items-center gap-2 text-sm font-semibold text-gray-800">
          <span aria-hidden>🗺️</span> Classroom Heatmap
        </p>
        <div className="flex items-center gap-3 text-[11px] text-gray-400">
          {LEGEND.map(([color, label]) => (
            <span key={label} className="flex items-center gap-1">
              <span className={`h-2 w-2 rounded-full ${color}`} aria-hidden />
              {label}
            </span>
          ))}
        </div>
      </div>

      {active !== 'none' && (
        <div className="mb-2 flex items-center gap-2 rounded-lg bg-violet-50 px-3 py-2 text-xs font-medium text-violet-700">
          <span aria-hidden>👆</span> {banner[active]}
        </div>
      )}
      <div
        ref={wrapperRef}
        onClick={handleWrapperClick}
        className={`relative w-full select-none overflow-hidden rounded-2xl bg-gray-100 ring-1 ring-black/5 ${cursorClass}`}
      >
        {result.heatmap_image ? (
          <img
            src={`data:image/png;base64,${result.heatmap_image}`}
            alt="Classroom heatmap"
            className="block w-full"
            draggable={false}
          />
        ) : (
          <div className="flex aspect-video items-center justify-center text-sm text-gray-400">
            No seats detected to render a heatmap.
          </div>
        )}

        {result.seats.map((seat) => {
          const isSelected = seat.seat_id === selectedSeatId
          const isCompared = comparisonSeatIds.includes(seat.seat_id)
          const isMoving = seat.seat_id === movingSeatId
          const left = seat.bbox.x1 * 100
          const top = seat.bbox.y1 * 100
          const width = (seat.bbox.x2 - seat.bbox.x1) * 100
          const height = (seat.bbox.y2 - seat.bbox.y1) * 100
          return (
            <button
              key={seat.seat_id}
              onClick={(e) => {
                e.stopPropagation()
                if (active === 'none') onSelectSeat(seat.seat_id)
              }}
              style={{ left: `${left}%`, top: `${top}%`, width: `${width}%`, height: `${height}%` }}
              className={`absolute rounded-md border-2 transition-all
                ${isMoving ? 'border-amber-400 ring-2 ring-amber-400 animate-pulse' : isSelected ? 'border-white ring-2 ring-violet-500' : isCompared ? 'border-white ring-2 ring-sky-500' : 'border-transparent hover:border-white/70'}`}
              aria-label={`Seat ${seat.seat_id}`}
            />
          )
        })}

        {result.instructor && (
          <div
            style={{
              left: `${result.instructor.position[0] * 100}%`,
              top: `${result.instructor.position[1] * 100}%`,
            }}
            className="pointer-events-none absolute -translate-x-1/2 -translate-y-1/2 text-xl drop-shadow"
            aria-label="Instructor position"
          >
            🧑‍🏫
          </div>
        )}

        {result.board_position && (
          <div
            style={{
              left: `${result.board_position[0] * 100}%`,
              top: `${result.board_position[1] * 100}%`,
            }}
            className="pointer-events-none absolute -translate-x-1/2 -translate-y-1/2 text-xl drop-shadow"
            aria-label="Board position"
          >
            🖼️
          </div>
        )}
      </div>
    </div>
  )
}
