import { Link } from 'react-router-dom'

export function AppHeader() {
  return (
    <header className="sticky top-0 z-20 border-b border-black/5 bg-white/70 backdrop-blur-md">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-3">
        <Link to="/" className="flex items-center gap-2">
          <span className="flex h-8 w-8 items-center justify-center rounded-xl bg-gradient-to-br from-violet-600 to-sky-500 text-sm font-bold text-white shadow-sm">
            CS
          </span>
          <span className="text-sm font-semibold tracking-tight text-gray-900">ClassSight AI</span>
        </Link>
        <span className="hidden text-xs text-gray-400 sm:block">Estimates, not guarantees</span>
      </div>
    </header>
  )
}
