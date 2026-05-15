"""FastAPI application factory."""

from __future__ import annotations

import asyncio
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from dodar.routes import scenarios, runs, scoring, reports, ws, playground, benchmark


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.active_runs: dict[str, asyncio.Task] = {}
    yield
    for task in app.state.active_runs.values():
        task.cancel()


app = FastAPI(
    title="DODAR Validation Benchmark",
    version="0.1.0",
    lifespan=lifespan,
)

# In production the frontend is served from the same origin so CORS is only
# needed for local dev. CORS_ORIGINS env var can override (comma-separated).
_dev_origins = ["http://localhost:5173", "http://localhost:5174", "http://localhost:3000"]
_cors_origins_env = os.environ.get("CORS_ORIGINS", "")
_cors_origins = [o.strip() for o in _cors_origins_env.split(",") if o.strip()] or _dev_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return JSONResponse({"status": "ok"})


# API routes
app.include_router(playground.router, prefix="/api")
app.include_router(scenarios.router, prefix="/api")
app.include_router(runs.router, prefix="/api")
app.include_router(scoring.router, prefix="/api")
app.include_router(reports.router, prefix="/api")
app.include_router(ws.router, prefix="/api")
app.include_router(benchmark.router, prefix="/api")

# Serve frontend static files in production
_frontend_dist = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if _frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(_frontend_dist), html=True), name="frontend")
