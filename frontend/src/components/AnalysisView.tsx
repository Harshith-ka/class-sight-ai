import { useEffect, useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { HeatmapCanvas } from './HeatmapCanvas'
import { SeatDetailPanel } from './SeatDetailPanel'
import { SeatRankingList } from './SeatRankingList'
import { StatsPanel } from './StatsPanel'
import { ConfidenceBreakdown } from './ConfidenceBreakdown'
import { ComparisonPanel } from './ComparisonPanel'
import { CorrectionToolbar } from './CorrectionToolbar'
import { ExportTrainingData } from './ExportTrainingData'
import {
  ApiError,
  correctBoard,
  correctInstructor,
  correctSeat,
  createSeat,
  deleteAnalysis,
  exportTrainingData,
  getAnalysis,
  moveSeat,
} from '../services/api'
import type { AnalysisResponse, CorrectionMode } from '../types/analysis'

interface Props {
  analysisId: string
  /** Hide the "Classroom Analysis" title + "New analysis" link when embedded
   * inside a page (e.g. BatchPage) that already provides its own header. */
  showHeader?: boolean
}

// Local component state, not global: this view is remounted (via `key`) any
// time analysisId changes — in the standalone route and when switching
// photos in BatchPage — so state naturally resets instead of leaking
// between analyses.
export function AnalysisView({ analysisId, showHeader = true }: Props) {
  const navigate = useNavigate()

  const [result, setResult] = useState<AnalysisResponse | null>(null)
  const [selectedSeatId, setSelectedSeatId] = useState<string | null>(null)
  const [comparisonSeatIds, setComparisonSeatIds] = useState<string[]>([])
  const [correctionMode, setCorrectionMode] = useState<CorrectionMode>('none')
  const [movingSeatId, setMovingSeatId] = useState<string | null>(null)
  const [exportMessage, setExportMessage] = useState<string | null>(null)

  const query = useQuery({
    queryKey: ['analysis', analysisId],
    queryFn: () => getAnalysis(analysisId),
    retry: false,
  })

  useEffect(() => {
    if (query.data) setResult(query.data)
  }, [query.data])

  const toggleComparisonSeat = (seatId: string) => {
    setComparisonSeatIds((current) => {
      if (current.includes(seatId)) return current.filter((id) => id !== seatId)
      if (current.length < 2) return [...current, seatId]
      return [current[1], seatId]
    })
  }

  const applyUpdate = (data: AnalysisResponse) => {
    setResult(data)
    setCorrectionMode('none')
    setMovingSeatId(null)
  }

  // Adding, deleting, or moving a seat re-clusters rows and reassigns every
  // seat_id (row_clustering.py relabels A1/A2/... from scratch), so any
  // previously selected/compared seat_id may now point at a different seat.
  // Clear selection state whenever the seat list is structurally rebuilt.
  const applyStructuralUpdate = (data: AnalysisResponse) => {
    applyUpdate(data)
    setSelectedSeatId(null)
    setComparisonSeatIds([])
  }

  const instructorMutation = useMutation({
    mutationFn: (vars: { x: number; y: number }) => correctInstructor(analysisId, vars.x, vars.y),
    onSuccess: applyUpdate,
  })

  const boardMutation = useMutation({
    mutationFn: (vars: { x: number; y: number }) => correctBoard(analysisId, vars.x, vars.y),
    onSuccess: applyUpdate,
  })

  const seatMutation = useMutation({
    mutationFn: (vars: { seatId: string; body: { occupied?: boolean; delete?: boolean } }) =>
      correctSeat(analysisId, vars.seatId, vars.body),
    onSuccess: (data, vars) => (vars.body.delete ? applyStructuralUpdate(data) : applyUpdate(data)),
  })

  const addSeatMutation = useMutation({
    mutationFn: (vars: { x1: number; y1: number; x2: number; y2: number }) => createSeat(analysisId, vars),
    onSuccess: applyStructuralUpdate,
  })

  const moveSeatMutation = useMutation({
    mutationFn: (vars: { seatId: string; x: number; y: number }) => moveSeat(analysisId, vars.seatId, vars.x, vars.y),
    onSuccess: applyStructuralUpdate,
  })

  const deleteMutation = useMutation({
    mutationFn: () => deleteAnalysis(analysisId),
    onSuccess: () => navigate('/'),
  })

  const exportMutation = useMutation({
    mutationFn: () => exportTrainingData(analysisId),
    onSuccess: (data) => {
      setExportMessage(
        `Saved ${data.seat_count} seat${data.seat_count === 1 ? '' : 's'}` +
          (data.instructor_included ? ' + instructor' : '') +
          ' to ml/training_data/.',
      )
    },
    onError: (err) => {
      setExportMessage(err instanceof ApiError ? err.message : 'Export failed.')
    },
  })

  const busy =
    instructorMutation.isPending ||
    boardMutation.isPending ||
    seatMutation.isPending ||
    addSeatMutation.isPending ||
    moveSeatMutation.isPending

  if (!result && query.isLoading) {
    return <div className="p-16 text-center text-gray-400">Loading analysis…</div>
  }

  if (!result && query.isError) {
    return (
      <div className="mx-auto max-w-lg p-16 text-center">
        <p className="mb-4 text-gray-600">
          This analysis could not be found. It may have expired (analyses are kept in memory only,
          not stored permanently).
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

  if (!result) return null

  const selectedSeat = result.seats.find((s) => s.seat_id === selectedSeatId) ?? null
  const comparisonSeats = result.seats.filter((s) => comparisonSeatIds.includes(s.seat_id))

  const handleCanvasClick = (x: number, y: number) => {
    if (movingSeatId) {
      moveSeatMutation.mutate({ seatId: movingSeatId, x, y })
    } else if (correctionMode === 'move-instructor') {
      instructorMutation.mutate({ x, y })
    } else if (correctionMode === 'move-board') {
      boardMutation.mutate({ x, y })
    } else if (correctionMode === 'add-seat') {
      const halfW = 0.04
      const halfH = 0.06
      addSeatMutation.mutate({
        x1: Math.max(0, x - halfW),
        y1: Math.max(0, y - halfH),
        x2: Math.min(1, x + halfW),
        y2: Math.min(1, y + halfH),
      })
    }
  }

  return (
    <div className="animate-fade-in-up">
      {showHeader && (
        <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight text-gray-900">Classroom Analysis</h1>
            <p className="text-sm text-gray-400">
              {result.stats.seats_detected} seat{result.stats.seats_detected === 1 ? '' : 's'} detected ·{' '}
              {Math.round(result.confidence_breakdown.overall)}% overall confidence
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button
              disabled={deleteMutation.isPending}
              onClick={() => {
                if (window.confirm('Delete this analysis? This removes it from memory immediately.')) {
                  deleteMutation.mutate()
                }
              }}
              className="rounded-lg border border-transparent px-3 py-1.5 text-sm text-red-400 transition-colors hover:border-red-100 hover:bg-red-50 hover:text-red-600 disabled:opacity-50"
            >
              Delete Analysis
            </button>
            <button
              onClick={() => navigate('/')}
              className="rounded-lg border border-gray-200 bg-white/70 px-3 py-1.5 text-sm text-gray-600 backdrop-blur transition-colors hover:bg-white hover:text-gray-900"
            >
              New analysis
            </button>
          </div>
        </div>
      )}

      {result.instructor_needs_manual && (
        <div className="mb-6 flex items-start gap-3 rounded-xl border border-amber-100 bg-amber-50 px-4 py-3 text-sm text-amber-700">
          <span className="mt-0.5 text-base" aria-hidden>
            ⚠️
          </span>
          <span>
            Instructor position could not be determined reliably. Use "Move Instructor" below to set
            it manually.
          </span>
        </div>
      )}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          <StatsPanel result={result} />
          <ConfidenceBreakdown breakdown={result.confidence_breakdown} />
          <CorrectionToolbar
            mode={correctionMode}
            onChange={(mode) => {
              setMovingSeatId(null)
              setCorrectionMode(mode)
            }}
          />
          <ExportTrainingData
            onExport={() => {
              setExportMessage(null)
              exportMutation.mutate()
            }}
            exporting={exportMutation.isPending}
            lastMessage={exportMessage}
            disabled={result.seats.length === 0}
          />
          <HeatmapCanvas
            result={result}
            selectedSeatId={selectedSeatId}
            comparisonSeatIds={comparisonSeatIds}
            correctionMode={correctionMode}
            movingSeatId={movingSeatId}
            onSelectSeat={setSelectedSeatId}
            onCanvasClick={handleCanvasClick}
          />
          <SeatRankingList seats={result.seats} selectedSeatId={selectedSeatId} onSelectSeat={setSelectedSeatId} />
        </div>

        <div className="space-y-6">
          <SeatDetailPanel
            seat={selectedSeat}
            busy={busy}
            onMarkOccupied={(seatId, occupied) => seatMutation.mutate({ seatId, body: { occupied } })}
            onDelete={(seatId) => seatMutation.mutate({ seatId, body: { delete: true } })}
            onAddToComparison={toggleComparisonSeat}
            onStartMove={(seatId) => {
              setCorrectionMode('none')
              setMovingSeatId((current) => (current === seatId ? null : seatId))
            }}
            isMoving={movingSeatId === selectedSeat?.seat_id}
          />
          <ComparisonPanel seats={comparisonSeats} onClear={() => setComparisonSeatIds([])} />
        </div>
      </div>
    </div>
  )
}
