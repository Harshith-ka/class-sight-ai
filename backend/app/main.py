from __future__ import annotations

import sys
from pathlib import Path

# Allow `import vision.*` to resolve to the sibling ../vision package without
# packaging it separately for Phase 1.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.analyze import router as analyze_router
from app.api.batch import router as batch_router
from app.api.export import router as export_router
from app.api.seats import router as seats_router
from app.core.config import CORS_ORIGINS

app = FastAPI(title="ClassSight AI API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analyze_router, prefix="/api")
app.include_router(seats_router, prefix="/api")
app.include_router(export_router, prefix="/api")
app.include_router(batch_router, prefix="/api")


@app.get("/api/health")
async def health() -> dict:
    return {"status": "ok"}
