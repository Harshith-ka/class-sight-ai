import { useParams } from 'react-router-dom'
import { AnalysisView } from '../components/AnalysisView'

export function AnalysisPage() {
  const { analysisId } = useParams<{ analysisId: string }>()
  if (!analysisId) return null

  return (
    <div className="mx-auto max-w-6xl px-6 py-10">
      <AnalysisView key={analysisId} analysisId={analysisId} />
    </div>
  )
}
