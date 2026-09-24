import { useCallback, useRef, useState } from 'react'

interface Props {
  onFilesSelected: (files: File[]) => void
  disabled?: boolean
  multiple?: boolean
  minFiles?: number
  maxFiles?: number
}

const ACCEPTED_TYPES = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp']
const MAX_FILE_BYTES = 10 * 1024 * 1024

export function UploadDropzone({ onFilesSelected, disabled, multiple = false, minFiles = 1, maxFiles = 6 }: Props) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [dragActive, setDragActive] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const validateAndEmit = useCallback(
    (fileList: FileList | null) => {
      if (!fileList || fileList.length === 0) return
      const files = Array.from(fileList).slice(0, multiple ? maxFiles : 1)

      for (const file of files) {
        if (!ACCEPTED_TYPES.includes(file.type)) {
          setError('Unsupported file type. Please upload JPG, PNG, or WEBP images.')
          return
        }
        if (file.size > MAX_FILE_BYTES) {
          setError(`"${file.name}" is too large. Maximum size is 10 MB per photo.`)
          return
        }
      }
      if (multiple && files.length < minFiles) {
        setError(`Select at least ${minFiles} photos for a batch.`)
        return
      }

      setError(null)
      onFilesSelected(files)
    },
    [multiple, minFiles, maxFiles, onFilesSelected],
  )

  return (
    <div className="w-full">
      <div
        role="button"
        tabIndex={0}
        aria-disabled={disabled}
        onClick={() => !disabled && inputRef.current?.click()}
        onKeyDown={(e) => e.key === 'Enter' && !disabled && inputRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault()
          if (!disabled) setDragActive(true)
        }}
        onDragLeave={() => setDragActive(false)}
        onDrop={(e) => {
          e.preventDefault()
          setDragActive(false)
          if (!disabled) validateAndEmit(e.dataTransfer.files)
        }}
        className={`group relative flex flex-col items-center justify-center gap-3 overflow-hidden rounded-3xl border-2 border-dashed px-8 py-16 text-center transition-all cursor-pointer
          ${dragActive ? 'scale-[1.01] border-violet-400 bg-violet-50/70 shadow-lg shadow-violet-100' : 'border-gray-300 bg-white/70 backdrop-blur hover:border-violet-300 hover:bg-violet-50/30'}
          ${disabled ? 'pointer-events-none opacity-60' : ''}`}
      >
        <div
          className={`flex h-16 w-16 items-center justify-center rounded-2xl text-3xl shadow-sm transition-transform
            ${dragActive ? 'scale-110 bg-violet-100' : 'bg-gray-50 group-hover:scale-105 group-hover:bg-violet-50'}`}
        >
          📷
        </div>
        <p className="text-lg font-medium text-gray-800">
          {multiple ? `Upload ${minFiles}-${maxFiles} Classroom Photos` : 'Upload Classroom Image'}
        </p>
        <p className="text-sm text-gray-500">
          {multiple
            ? 'Different angles of the same room — drag & drop or click to browse'
            : 'Drag & drop or click to browse'}
        </p>
        <div className="mt-2 flex gap-2 text-xs font-medium text-gray-400">
          <span className="rounded-full border border-gray-200 bg-white px-2 py-1">JPG</span>
          <span className="rounded-full border border-gray-200 bg-white px-2 py-1">PNG</span>
          <span className="rounded-full border border-gray-200 bg-white px-2 py-1">WEBP</span>
        </div>
        <input
          ref={inputRef}
          type="file"
          multiple={multiple}
          accept={ACCEPTED_TYPES.join(',')}
          className="hidden"
          onChange={(e) => validateAndEmit(e.target.files)}
        />
      </div>
      {error && (
        <p className="mt-3 flex items-center gap-1.5 text-sm text-red-600">
          <span aria-hidden>⚠️</span> {error}
        </p>
      )}
      <p className="mt-4 text-center text-xs text-gray-400">
        Your classroom image{multiple ? 's are' : ' is'} analyzed for computer-vision processing.
        Avoid uploading images containing people who have not consented to image processing.
      </p>
    </div>
  )
}
