"""TraceFace FastAPI application entry point.

Boots the async REST + SSE surface over the biometric OSINT / Web3 provenance
pipeline in ``src/``, and serves the dark cyber-forensic dashboard UI from
``frontend/dist``.
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles

from api import __version__
from api.dependencies import warm_up
from api.routers import graph, scan, takedown, verify, zk
from api.schemas.common import HealthResponse
from api.metrics import PrometheusMiddleware, metrics_endpoint, init_app_info

logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("web3").setLevel(logging.WARNING)
logger = logging.getLogger("traceface.api")

_default_origins = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:8000,http://127.0.0.1:8000"
CORS_ORIGINS = [
    o.strip()
    for o in os.getenv("TRACEFACE_CORS_ORIGINS", _default_origins).split(",")
    if o.strip()
]

WARMUP_ON_BOOT = os.getenv("TRACEFACE_WARMUP", "0") == "1"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    if WARMUP_ON_BOOT:
        logger.info("Warming up vision models on boot...")
        try:
            warm_up()
            logger.info("Vision models loaded.")
        except Exception as exc:  # noqa: BLE001
            logger.warning("Vision warmup failed: %s", exc)
    yield


app = FastAPI(
    title="TraceFace API",
    version=__version__,
    description=(
        "Biometric OSINT & Blockchain Provenance pipeline exposed over REST + SSE. "
        "Face extraction, frequency-domain liveness, reverse-image OSINT, 4-leaf "
        "Merkle sealing, EIP-712 takedowns, and Groth16 zero-knowledge biometric proofs."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize metrics collection
app.add_middleware(PrometheusMiddleware)
init_app_info(__version__)

API_PREFIX = "/api/v1"
app.include_router(scan.router, prefix=API_PREFIX)
app.include_router(verify.router, prefix=API_PREFIX)
app.include_router(graph.router, prefix=API_PREFIX)
app.include_router(zk.router, prefix=API_PREFIX)
app.include_router(takedown.router, prefix=API_PREFIX)

# Metrics endpoint for Prometheus
@app.get("/metrics", tags=["meta"])
async def metrics():
    """Prometheus metrics endpoint."""
    from starlette.responses import PlainTextResponse
    from prometheus_client import generate_latest
    return PlainTextResponse(
        generate_latest(),
        media_type="text/plain; version=0.0.4; charset=utf-8"
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    message = str(exc)
    error_code = None
    if message.startswith("ERR_") or ":" in message:
        head = message.split(":", 1)[0].strip()
        if head.startswith("ERR_") or head.isupper():
            error_code = head
    return JSONResponse(
        status_code=422,
        content={"detail": message, "error_code": error_code},
    )


@app.get("/health", response_model=HealthResponse, tags=["meta"])
async def health() -> HealthResponse:
    from api import dependencies

    vision_loaded = dependencies._vision_pipeline is not None
    blockchain_connected = False
    contract_deployed = False
    try:
        from src.blockchain.client import BlockchainClient

        client = BlockchainClient()
        blockchain_connected = client.is_connected()
        contract_deployed = client.contract is not None
    except Exception:  # noqa: BLE001
        pass

    return HealthResponse(
        version=__version__,
        vision_loaded=vision_loaded,
        blockchain_connected=blockchain_connected,
        contract_deployed=contract_deployed,
    )


# Mount static production UI from frontend/dist if built
frontend_dist = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "dist")
frontend_assets = os.path.join(frontend_dist, "assets")

if os.path.exists(frontend_assets):
    app.mount("/assets", StaticFiles(directory=frontend_assets), name="assets")


@app.get("/favicon.svg", tags=["ui"])
async def favicon():
    fav = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "public", "favicon.svg")
    if os.path.exists(fav):
        return FileResponse(fav, media_type="image/svg+xml")
    return Response(
        content='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10" fill="#06b6d4"/></svg>',
        media_type="image/svg+xml",
    )


@app.get("/", tags=["ui"])
async def serve_ui():
    index_file = os.path.join(frontend_dist, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {
        "service": "traceface-api",
        "version": __version__,
        "docs": "/docs",
        "health": "/health",
        "notice": "Frontend build not detected in frontend/dist. Run 'npm run build' in frontend/ to compile UI.",
    }
