interface Props {
  onExport: () => void
  exporting: boolean
  lastMessage: string | null
  disabled: boolean
}

export function ExportTrainingData({ onExport, exporting, lastMessage, disabled }: Props) {
  return (
    <div className="card flex flex-wrap items-center gap-3 p-4">
      <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-gray-900/5 text-base" aria-hidden>
        💾
      </span>
      <div className="flex-1">
        <p className="text-sm font-medium text-gray-700">Export training data</p>
        <p className="text-xs text-gray-400">
          Saves this image and its current seats/instructor (including any corrections you've made)
          to <code className="rounded bg-gray-100 px-1 py-0.5">ml/training_data/</code> on this
          machine, in YOLO label format — nothing leaves your computer. Used to fine-tune a
          classroom-specific detector later.
        </p>
      </div>
      <button
        onClick={onExport}
        disabled={disabled || exporting}
        className="shrink-0 rounded-lg bg-gray-900 px-3 py-1.5 text-xs font-medium text-white transition-colors hover:bg-gray-700 disabled:opacity-50"
      >
        {exporting ? 'Exporting…' : 'Export Training Data'}
      </button>
      {lastMessage && (
        <p className="flex w-full items-center gap-1.5 text-xs text-emerald-600">
          <span aria-hidden>✓</span> {lastMessage}
        </p>
      )}
    </div>
  )
}
