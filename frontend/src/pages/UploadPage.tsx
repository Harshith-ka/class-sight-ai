import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { UploadDropzone } from '../components/UploadDropzone'
import { ProcessingChecklist } from '../components/ProcessingChecklist'
import { uploadImage, uploadBatch, ApiError } from '../services/api'

type Mode = 'single' | 'batch'

export function UploadPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [mode, setMode] = useState<Mode>('single')
  const [error, setError] = useState<string | null>(null)

  const singleMutation = useMutation({
    mutationFn: uploadImage,
    onSuccess: (data) => {
      queryClient.setQueryData(['analysis', data.analysis_id], data)
      navigate(`/analysis/${data.analysis_id}`)
    },
    onError: (err) => {
      setError(err instanceof ApiError ? err.message : 'Something went wrong. Please try again.')
    },
  })

  const batchMutation = useMutation({
    mutationFn: uploadBatch,
    onSuccess: (data) => {
      queryClient.setQueryData(['batch', data.batch_id], data)
      navigate(`/batch/${data.batch_id}`)
    },
    onError: (err) => {
      setError(err instanceof ApiError ? err.message : 'Something went wrong. Please try again.')
    },
  })

  const pending = singleMutation.isPending || batchMutation.isPending

  if (pending) {
    return (
      <div className="flex min-h-[calc(100vh-57px)] items-center justify-center px-6">
        <ProcessingChecklist done={false} />
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-2xl px-6 py-16 sm:py-20">
      <div className="animate-fade-in-up mb-10 text-center">
        <span className="mb-4 inline-flex items-center gap-1.5 rounded-full border border-violet-100 bg-violet-50 px-3 py-1 text-xs font-medium text-violet-700">
          <span aria-hidden>✨</span> Computer-vision seat visibility analysis
        </span>
        <h1 className="mb-3 text-4xl font-semibold tracking-tight text-gray-900 sm:text-5xl">
          See your classroom
          <br />
          <span className="bg-gradient-to-r from-violet-600 to-sky-500 bg-clip-text text-transparent">
            the way the board does
          </span>
        </h1>
        <p className="mx-auto max-w-md text-gray-500">
          Upload a photo and get an estimated exposure score for every seat — plus a heatmap,
          rankings, and full explanations. Estimates, not guarantees.
        </p>
      </div>

      <div className="animate-fade-in-up mb-6 flex justify-center" style={{ animationDelay: '0.05s' }}>
        <div className="inline-flex rounded-xl border border-gray-200 bg-white/70 p-1 shadow-sm backdrop-blur">
          <button
            onClick={() => {
              setMode('single')
              setError(null)
            }}
            className={`rounded-lg px-4 py-1.5 text-sm font-medium transition-all
              ${mode === 'single' ? 'bg-violet-600 text-white shadow-sm' : 'text-gray-600 hover:text-gray-900'}`}
          >
            Single Photo
          </button>
          <button
            onClick={() => {
              setMode('batch')
              setError(null)
            }}
            className={`rounded-lg px-4 py-1.5 text-sm font-medium transition-all
              ${mode === 'batch' ? 'bg-violet-600 text-white shadow-sm' : 'text-gray-600 hover:text-gray-900'}`}
          >
            Multiple Photos
          </button>
        </div>
      </div>

      {mode === 'batch' && (
        <p className="animate-fade-in-up mb-4 rounded-xl bg-violet-50 px-4 py-3 text-center text-xs text-violet-700">
          Each photo is analyzed independently — a seat hidden behind a desk from one angle might
          be clearly visible from another. This isn't a 3D merge of the photos, just a way to see
          all your angles together.
        </p>
      )}

      <div className="animate-fade-in-up" style={{ animationDelay: '0.1s' }}>
        {mode === 'single' ? (
          <UploadDropzone
            onFilesSelected={(files) => {
              setError(null)
              if (files[0]) singleMutation.mutate(files[0])
            }}
          />
        ) : (
          <UploadDropzone
            multiple
            minFiles={2}
            maxFiles={6}
            onFilesSelected={(files) => {
              setError(null)
              batchMutation.mutate(files)
            }}
          />
        )}
      </div>

      {error && (
        <p className="animate-fade-in-up mt-4 rounded-xl bg-red-50 px-4 py-3 text-sm text-red-600">
          {error}
        </p>
      )}

      <div className="animate-fade-in-up mt-12 grid grid-cols-3 gap-3 text-center" style={{ animationDelay: '0.15s' }}>
        {[
          { icon: '🎯', label: 'Per-seat exposure score' },
          { icon: '🗺️', label: 'Interactive heatmap' },
          { icon: '✏️', label: 'Fully correctable' },
        ].map((item) => (
          <div key={item.label} className="rounded-xl border border-gray-100 bg-white/60 px-2 py-4 backdrop-blur">
            <div className="mb-1 text-xl" aria-hidden>
              {item.icon}
            </div>
            <p className="text-xs font-medium text-gray-500">{item.label}</p>
          </div>
        ))}
      </div>
    </div>
  )
}
