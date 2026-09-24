// Shared score-band coloring so every score readout (seat detail, ranking,
// comparison) uses the same green/yellow/orange/red bands as the heatmap
// legend (vision/visibility/heatmap.py) — higher score = lower estimated
// exposure.
export function scoreBand(value: number): 'low' | 'medium' | 'elevated' | 'high' {
  if (value >= 75) return 'low'
  if (value >= 55) return 'medium'
  if (value >= 35) return 'elevated'
  return 'high'
}

const TEXT_CLASSES: Record<ReturnType<typeof scoreBand>, string> = {
  low: 'text-emerald-600',
  medium: 'text-amber-600',
  elevated: 'text-orange-600',
  high: 'text-rose-600',
}

const BG_CLASSES: Record<ReturnType<typeof scoreBand>, string> = {
  low: 'bg-emerald-500',
  medium: 'bg-amber-500',
  elevated: 'bg-orange-500',
  high: 'bg-rose-500',
}

const SOFT_BG_CLASSES: Record<ReturnType<typeof scoreBand>, string> = {
  low: 'bg-emerald-50 text-emerald-700',
  medium: 'bg-amber-50 text-amber-700',
  elevated: 'bg-orange-50 text-orange-700',
  high: 'bg-rose-50 text-rose-700',
}

export function scoreTextClass(value: number): string {
  return TEXT_CLASSES[scoreBand(value)]
}

export function scoreBgClass(value: number): string {
  return BG_CLASSES[scoreBand(value)]
}

export function scoreSoftBgClass(value: number): string {
  return SOFT_BG_CLASSES[scoreBand(value)]
}
