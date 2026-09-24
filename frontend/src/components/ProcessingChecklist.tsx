import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'

const STEPS = [
  'Image quality checked',
  'Classroom detected',
  'Students detected',
  'Instructor detected',
  'Seats detected',
  'Seating arrangement mapped',
  'Visibility calculated',
  'Heatmap generated',
]

interface Props {
  done: boolean
}

export function ProcessingChecklist({ done }: Props) {
  const [visible, setVisible] = useState(1)

  useEffect(() => {
    if (done) {
      setVisible(STEPS.length)
      return
    }
    const id = setInterval(() => {
      setVisible((v) => (v < STEPS.length - 1 ? v + 1 : v))
    }, 500)
    return () => clearInterval(id)
  }, [done])

  const progress = Math.round((visible / STEPS.length) * 100)

  return (
    <div className="card mx-auto w-full max-w-md p-8">
      <div className="mb-6 flex flex-col items-center gap-3">
        <motion.div
          animate={{ rotate: done ? 0 : 360 }}
          transition={done ? {} : { repeat: Infinity, duration: 1.6, ease: 'linear' }}
          className={`flex h-12 w-12 items-center justify-center rounded-2xl text-xl shadow-sm
            ${done ? 'bg-emerald-100' : 'bg-violet-100'}`}
        >
          {done ? '✅' : '🔍'}
        </motion.div>
        <p className="text-lg font-medium text-gray-800">Analyzing Classroom...</p>
        <div className="h-1.5 w-full overflow-hidden rounded-full bg-gray-100">
          <motion.div
            className="h-full rounded-full bg-gradient-to-r from-violet-500 to-sky-500"
            animate={{ width: `${progress}%` }}
            transition={{ duration: 0.3 }}
          />
        </div>
      </div>
      <ul className="space-y-3">
        {STEPS.map((step, i) => {
          const isVisible = i < visible
          const isChecked = i < visible - (done ? 0 : 1) || done
          return (
            <motion.li
              key={step}
              initial={{ opacity: 0, x: -8 }}
              animate={{ opacity: isVisible ? 1 : 0.25, x: 0 }}
              transition={{ duration: 0.3 }}
              className="flex items-center gap-3 text-sm"
            >
              <span
                className={`flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-xs transition-colors
                  ${isChecked ? 'bg-emerald-500 text-white' : 'border border-gray-300 text-transparent'}`}
              >
                ✓
              </span>
              <span className={isChecked ? 'text-gray-800' : 'text-gray-400'}>{step}</span>
            </motion.li>
          )
        })}
      </ul>
      {done && (
        <p className="mt-6 text-center text-sm font-medium text-emerald-600">Analysis Complete</p>
      )}
    </div>
  )
}
