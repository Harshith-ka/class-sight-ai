import { Route, Routes } from 'react-router-dom'
import { AppHeader } from './components/AppHeader'
import { UploadPage } from './pages/UploadPage'
import { AnalysisPage } from './pages/AnalysisPage'
import { BatchPage } from './pages/BatchPage'

export default function App() {
  return (
    <div className="min-h-screen">
      <AppHeader />
      <Routes>
        <Route path="/" element={<UploadPage />} />
        <Route path="/analysis/:analysisId" element={<AnalysisPage />} />
        <Route path="/batch/:batchId" element={<BatchPage />} />
      </Routes>
    </div>
  )
}
