# ClassSight AI — Phase 1 (MVP)

AI-powered classroom seat visibility analyzer. Upload a classroom photo and
get per-seat exposure scores, an interactive heatmap, and manual correction
tools. Phase 1 uses pretrained YOLO + geometric heuristics (no custom
training, no database) — see the roadmap below.

**Results are computer-vision estimates, not a guarantee of what an
instructor can or cannot see.**

## Stack

- `vision/` — detection, geometry, seat/row clustering, visibility scoring,
  heatmap generation. Pure Python, framework-agnostic, unit tested.
- `backend/` — FastAPI. Stateless: analyses live in server memory for 30
  minutes, nothing is written to disk (see `app/services/session_store.py`).
- `frontend/` — React + TypeScript + Vite + Tailwind + React Query + Zustand.

## Running locally

Backend (from `classsight-ai/`):

```bash
python -m venv .venv
./.venv/Scripts/pip install -r backend/requirements.txt
./.venv/Scripts/python -m uvicorn app.main:app --app-dir backend --reload --port 8000
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Then open http://localhost:5173. The first analysis request downloads YOLO
weights (yolov8n.pt) automatically and takes longer than subsequent ones.

## Tests

```bash
./.venv/Scripts/python -m pytest tests/
```

## Roadmap

Phase 1 (this codebase) covers upload → detect → score → heatmap →
interactive dashboard → manual correction, stateless. Planned next:

- **Phase 2**: PostgreSQL + auth + analysis history + face blurring.
- **Phase 3**: Custom classroom dataset + fine-tuned detector (occupied/empty
  chair, instructor classes) replacing the current heuristics.
- **Phase 4**: Video/real-time tracking, multi-camera fusion, layout editor.

See the full original product spec for details on each phase.
