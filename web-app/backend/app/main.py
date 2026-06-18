"""FastAPI application entry point.

Run from ``web-app/backend``::

    uvicorn app.main:app --reload --port 8000

Then open http://localhost:8000 — the frontend is served by this same process
(StaticFiles mount), so there is no separate server and no CORS hassle. CORS is
still configured for the case where the frontend is served from another origin
(see ``config.ALLOWED_ORIGINS``).
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from . import config
from .routers import simulation

app = FastAPI(
    title="LIF Neuron Simulator API",
    version="0.1.0",
    description="REST API around the lif_core simulation engine.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(simulation.router)

# Serve the static frontend (web-app/frontend) at the root, if present.
# app/main.py -> app -> backend -> web-app -> frontend
_FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"
if _FRONTEND_DIR.is_dir():
    app.mount(
        "/",
        StaticFiles(directory=str(_FRONTEND_DIR), html=True),
        name="frontend",
    )
