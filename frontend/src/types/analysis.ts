export interface BBox {
  x1: number
  y1: number
  x2: number
  y2: number
}

export interface SeatScores {
  distance: number
  occlusion: number
  angle: number
  position: number
  confidence: number
  final: number
  raw_visibility: number
}

export interface Seat {
  seat_id: string
  row_index: number
  col_index: number
  bbox: BBox
  occupied: boolean
  detection_confidence: number
  position_category: string
  manual: boolean
  scores: SeatScores
  explanation: string[]
}

export interface Instructor {
  position: [number, number]
  confidence: number
  source: 'heuristic' | 'manual'
  bbox: BBox | null
}

export interface Quality {
  resolution: string
  brightness: string
  sharpness: string
  contrast: string
  overall: number
  width: number
  height: number
  passed: boolean
  reasons: string[]
}

export interface Stats {
  seats_detected: number
  occupied: number
  empty: number
  instructor_detected: boolean
  average_visibility: number
  average_obstruction: number
}

export interface ConfidenceBreakdown {
  image_quality: number
  instructor_detection: number
  seat_detection: number
  overall: number
}

export interface AnalysisResponse {
  analysis_id: string
  quality: Quality
  instructor: Instructor | null
  instructor_needs_manual: boolean
  board_position: [number, number] | null
  seats: Seat[]
  stats: Stats
  heatmap_image: string | null
  overall_confidence: number
  confidence_breakdown: ConfidenceBreakdown
  image_width: number
  image_height: number
  detection_count: number
}

export interface BatchImageResult {
  analysis_id: string
  label: string
  analysis: AnalysisResponse
}

export interface BatchSummary {
  image_count: number
  seats_detected_min: number
  seats_detected_max: number
  most_seats_analysis_id: string | null
  note: string
}

export interface BatchResponse {
  batch_id: string
  images: BatchImageResult[]
  summary: BatchSummary
}

export type CorrectionMode = 'none' | 'move-instructor' | 'move-board' | 'add-seat'
