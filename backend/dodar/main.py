"""FastAPI application factory."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from dodar.routes import scenarios, runs, scoring, reports, ws


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Store active run tasks
    app.state.active_runs: dict[str, asyncio.Task] = {}
    yield
    # Cancel any active runs on shutdown
    for task in app.state.active_runs.values():
        task.cancel()


app = FastAPI(
    title="DODAR Validation Benchmark",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
app.include_router(scenarios.router, prefix="/api")
app.include_router(runs.router, prefix="/api")
app.include_router(scoring.router, prefix="/api")
app.include_router(reports.router, prefix="/api")
app.include_router(ws.router, prefix="/api")

# Serve frontend static files in production
_frontend_dist = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if _frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(_frontend_dist), html=True), name="frontend")
