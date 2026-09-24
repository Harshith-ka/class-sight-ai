import { useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate, useParams } from 'react-router-dom'
import { AnalysisView } from '../components/AnalysisView'
import { getBatch } from '../services/api'

export function BatchPage() {
  const { batchId } = useParams<{ batchId: string }>()
  const navigate = useNavigate()
  const [selectedId, setSelectedId] = useState<string | null>(null)

  const query = useQuery({
    queryKey: ['batch', batchId],
    queryFn: () => getBatch(batchId!),
    enabled: !!batchId,
    retry: false,
  })

  useEffect(() => {
    if (query.data && !selectedId) {
      setSelectedId(query.data.summary.most_seats_analysis_id ?? query.data.images[0]?.analysis_id ?? null)
    }
  }, [query.data, selectedId])

  if (!batchId) return null

  if (query.isLoading) {
    return <div className="p-16 text-center text-gray-400">Loading batch…</div>
  }

  if (query.isError || !query.data) {
    return (
      <div className="mx-auto max-w-lg p-16 text-center">
        <p className="mb-4 text-gray-600">
          This batch could not be found. It may have expired (kept in memory only, not stored
          permanently).
        </p>
        <button
          onClick={() => navigate('/')}
          className="rounded-lg bg-violet-600 px-4 py-2 text-sm font-medium text-white"
        >
          Start a new analysis
        </button>
      </div>
    )
  }

  const { images, summary } = query.data

  return (
    <div className="mx-auto max-w-6xl px-6 py-10">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-gray-900">Classroom Analysis — {images.length} Photos</h1>
        <button onClick={() => navigate('/')} className="text-sm text-gray-400 hover:text-gray-600">
          New analysis
        </button>
      </div>

      <div className="card mb-6 p-5">
        <div className="mb-3 flex flex-wrap gap-6">
          <div>
            <p className="text-xs uppercase tracking-wide text-gray-400">Photos</p>
            <p className="text-xl font-semibold text-gray-900">{summary.image_count}</p>
          </div>
          <div>
            <p className="text-xs uppercase tracking-wide text-gray-400">Seats seen (range)</p>
            <p className="text-xl font-semibold text-gray-900">
              {summary.seats_detected_min}–{summary.seats_detected_max}
            </p>
          </div>
        </div>
        <p className="text-xs text-gray-400">{summary.note}</p>
      </div>

      <div className="mb-6 flex flex-wrap gap-2">
        {images.map((img) => (
          <button
            key={img.analysis_id}
            onClick={() => setSelectedId(img.analysis_id)}
            className={`flex items-center gap-2 rounded-xl border px-3 py-2 text-sm transition-colors
              ${
                selectedId === img.analysis_id
                  ? 'border-violet-400 bg-violet-50 text-violet-700'
                  : 'border-gray-200 bg-white text-gray-600 hover:bg-gray-50'
              }`}
          >
            <span className="max-w-[10rem] truncate">{img.label}</span>
            <span className="rounded-full bg-gray-100 px-2 py-0.5 text-xs font-medium text-gray-500">
              {img.analysis.seats.length} seats
            </span>
            {img.analysis_id === summary.most_seats_analysis_id && (
              <span className="text-xs text-emerald-600" title="Most seats detected among your photos">
                ★
              </span>
            )}
          </button>
        ))}
      </div>

      {selectedId && <AnalysisView key={selectedId} analysisId={selectedId} showHeader={false} />}
    </div>
  )
}
