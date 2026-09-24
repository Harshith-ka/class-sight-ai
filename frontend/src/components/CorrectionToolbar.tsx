import type { CorrectionMode } from '../types/analysis'

interface Props {
  mode: CorrectionMode
  onChange: (mode: CorrectionMode) => void
}

export function CorrectionToolbar({ mode, onChange }: Props) {
  const toggle = (target: CorrectionMode) => onChange(mode === target ? 'none' : target)

  return (
    <div className="card flex flex-wrap items-center gap-2 p-4">
      <p className="mr-1 flex items-center gap-2 text-sm font-medium text-gray-600">
        <span aria-hidden>🛠️</span> Manual correction:
      </p>
      <button
        onClick={() => toggle('move-instructor')}
        className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-colors
          ${mode === 'move-instructor' ? 'bg-violet-600 text-white shadow-sm' : 'border border-gray-200 text-gray-700 hover:bg-gray-50'}`}
      >
        🧑‍🏫 Move Instructor
      </button>
      <button
        onClick={() => toggle('move-board')}
        className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-colors
          ${mode === 'move-board' ? 'bg-violet-600 text-white shadow-sm' : 'border border-gray-200 text-gray-700 hover:bg-gray-50'}`}
      >
        🖼️ Mark Board
      </button>
      <button
        onClick={() => toggle('add-seat')}
        className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-colors
          ${mode === 'add-seat' ? 'bg-violet-600 text-white shadow-sm' : 'border border-gray-200 text-gray-700 hover:bg-gray-50'}`}
      >
        ➕ Add Seat
      </button>
      <span className="text-xs text-gray-400">
        Select a seat on the heatmap for occupied/empty, move, and delete actions.
      </span>
    </div>
  )
}
