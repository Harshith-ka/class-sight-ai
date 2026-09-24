import type { ConfidenceBreakdown as ConfidenceBreakdownData } from '../types/analysis'
import { ScoreBar } from './ScoreBar'
import { scoreSoftBgClass } from '../utils/score'

interface Props {
  breakdown: ConfidenceBreakdownData
}

// Only genuinely-computed components are shown here — no fabricated
// "Student Detection" or "Classroom Mapping" numbers we have no real
// independent signal for (matches vision/pipeline.py's confidence_breakdown).
export function ConfidenceBreakdown({ breakdown }: Props) {
  return (
    <div className="card p-6">
      <div className="mb-3 flex items-center justify-between">
        <p className="flex items-center gap-2 text-sm font-semibold text-gray-800">
          <span aria-hidden>🎯</span> Confidence
        </p>
        <span className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ${scoreSoftBgClass(breakdown.overall)}`}>
          {Math.round(breakdown.overall)}% overall
        </span>
      </div>
      <div className="space-y-2.5">
        <ScoreBar label="Image Quality" value={breakdown.image_quality} colorClass="bg-sky-500" />
        <ScoreBar label="Instructor Detection" value={breakdown.instructor_detection} colorClass="bg-violet-500" />
        <ScoreBar label="Seat Detection" value={breakdown.seat_detection} colorClass="bg-emerald-500" />
        <ScoreBar label="Overall Analysis" value={breakdown.overall} colorClass="bg-gray-800" />
      </div>
    </div>
  )
}
