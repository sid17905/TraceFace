"""Prometheus metrics collection for TraceFace API.

Exposes /metrics endpoint for Prometheus scraping.
"""

from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager
from typing import Callable

from prometheus_client import Counter, Gauge, Histogram, Info, generate_latest
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("traceface.metrics")

# HTTP Metrics
HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"]
)

HTTP_REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency",
    ["method", "endpoint"],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
)

HTTP_REQUESTS_IN_PROGRESS = Gauge(
    "http_requests_in_progress",
    "HTTP requests currently being processed",
    ["method"]
)

# OSINT Metrics
OSINT_REQUESTS_TOTAL = Counter(
    "osint_requests_total",
    "Total OSINT search requests",
    ["engine"]
)

OSINT_SUCCESS_TOTAL = Counter(
    "osint_success_total",
    "Total successful OSINT searches",
    ["engine"]
)

OSINT_FAILURE_TOTAL = Counter(
    "osint_failure_total",
    "Total failed OSINT searches",
    ["engine", "error_type"]
)

OSINT_CANDIDATES_TOTAL = Counter(
    "osint_candidates_total",
    "Total candidates discovered from OSINT",
    ["platform"]
)

OSINT_DURATION = Histogram(
    "osint_duration_seconds",
    "OSINT search latency",
    ["engine"],
    buckets=[1.0, 5.0, 10.0, 30.0, 60.0, 120.0]
)

OSINT_API_QUOTA_REMAINING = Gauge(
    "osint_api_quota_remaining",
    "Remaining API quota for OSINT services",
    ["service"]
)

# Vision Metrics
VISION_FACE_DETECTIONS_TOTAL = Counter(
    "vision_face_detections_total",
    "Total face detections",
    ["status"]
)

VISION_EMBEDDING_EXTRACTIONS_TOTAL = Counter(
    "vision_embedding_extractions_total",
    "Total embedding extractions"
)

VISION_LIVENESS_CHECKS_TOTAL = Counter(
    "vision_liveness_checks_total",
    "Total liveness checks",
    ["result"]
)

VISION_DURATION = Histogram(
    "vision_duration_seconds",
    "Vision pipeline latency",
    ["stage"],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0]
)

# Biometric Metrics
BIOMETRIC_VERIFICATIONS_TOTAL = Counter(
    "biometric_verifications_total",
    "Total biometric verifications"
)

BIOMETRIC_MATCHES_TOTAL = Counter(
    "biometric_matches_total",
    "Total biometric matches"
)

BIOMETRIC_REJECTIONS_TOTAL = Counter(
    "biometric_rejections_total",
    "Total biometric rejections below threshold"
)

BIOMETRIC_SIMILARITY = Histogram(
    "biometric_similarity_scores",
    "Distribution of similarity scores",
    buckets=[0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
)

# Blockchain Metrics
BLOCKCHAIN_TRANSACTIONS_TOTAL = Counter(
    "blockchain_transactions_total",
    "Total blockchain transactions",
    ["status"]
)

BLOCKCHAIN_GAS_USED = Counter(
    "blockchain_gas_used_total",
    "Total gas used"
)

BLOCKCHAIN_GAS_PRICE = Gauge(
    "blockchain_gas_price_gwei",
    "Current gas price in Gwei"
)

BLOCKCHAIN_ETH_BALANCE = Gauge(
    "blockchain_eth_balance",
    "Deployer account ETH balance"
)

BLOCKCHAIN_CLIENT_CONNECTED = Gauge(
    "blockchain_client_connected",
    "Whether blockchain client is connected"
)

# IPFS Metrics
IPFS_PINS_TOTAL = Counter(
    "ipfs_pins_total",
    "Total IPFS pins",
    ["status"]
)

IPFS_PIN_DURATION = Histogram(
    "ipfs_pin_duration_seconds",
    "IPFS pin latency",
    buckets=[0.1, 0.5, 1.0, 5.0, 10.0, 30.0]
)

IPFS_PINATA_QUOTA_REMAINING = Gauge(
    "ipfs_pinata_quota_remaining",
    "Remaining Pinata pin quota"
)

# Graph Storage Metrics
GRAPH_DB_SIZE = Gauge(
    "graph_db_size_bytes",
    "Graph database size in bytes"
)

GRAPH_NODES_TOTAL = Counter(
    "graph_nodes_total",
    "Total graph nodes created"
)

GRAPH_EDGES_TOTAL = Counter(
    "graph_edges_total",
    "Total graph edges created"
)

# Job Queue Metrics
QUEUED_SCANS_TOTAL = Gauge(
    "queued_scans_total",
    "Total queued scans"
)

ACTIVE_SCANS_TOTAL = Gauge(
    "active_scans_total",
    "Total active scans"
)

SCANS_TOTAL = Counter(
    "scans_total",
    "Total scans processed",
    ["status"]
)

# System Metrics
ACTIVE_SCAN_JOBS = Gauge(
    "active_scan_jobs",
    "Number of active scan jobs"
)

SCANS_COMPLETED_TOTAL = Counter(
    "scans_completed_total",
    "Total completed scans"
)

SCANS_FAILED_TOTAL = Counter(
    "scans_failed_total",
    "Total failed scans"
)

# Info Metrics
APP_INFO = Info(
    "traceface_app",
    "Application information"
)

class PrometheusMiddleware(BaseHTTPMiddleware):
    """Middleware to collect HTTP metrics."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        method = request.method
        endpoint = request.url.path

        # Skip metrics endpoint itself
        if endpoint == "/metrics":
            return await call_next(request)

        # Track in-progress requests
        HTTP_REQUESTS_IN_PROGRESS.labels(method=method).inc()

        # Time the request
        start_time = time.time()

        try:
            response = await call_next(request)
            status = response.status_code

            # Record metrics
            HTTP_REQUESTS_TOTAL.labels(
                method=method,
                endpoint=endpoint,
                status=status
            ).inc()

            HTTP_REQUEST_DURATION.labels(
                method=method,
                endpoint=endpoint
            ).observe(time.time() - start_time)

            return response

        except Exception as exc:
            # Record error
            HTTP_REQUESTS_TOTAL.labels(
                method=method,
                endpoint=endpoint,
                status=500
            ).inc()

            HTTP_REQUEST_DURATION.labels(
                method=method,
                endpoint=endpoint
            ).observe(time.time() - start_time)

            raise

        finally:
            HTTP_REQUESTS_IN_PROGRESS.labels(method=method).dec()


async def metrics_endpoint(request: Request) -> Response:
    """Prometheus metrics endpoint."""
    from starlette.responses import PlainTextResponse

    return PlainTextResponse(
        generate_latest(),
        media_type="text/plain; version=0.0.4; charset=utf-8"
    )


def init_app_info(version: str = "1.0.0") -> None:
    """Initialize application info metric."""
    APP_INFO.info({
        "version": version,
        "service": "traceface-api"
    })


@asynccontextmanager
async def track_osint_engine(engine: str):
    """Track OSINT engine execution."""
    OSINT_REQUESTS_TOTAL.labels(engine=engine).inc()
    start = time.time()
    try:
        yield
        OSINT_SUCCESS_TOTAL.labels(engine=engine).inc()
    except Exception as exc:
        OSINT_FAILURE_TOTAL.labels(
            engine=engine,
            error_type=type(exc).__name__
        ).inc()
        raise
    finally:
        OSINT_DURATION.labels(engine=engine).observe(time.time() - start)


def track_vision_stage(stage: str):
    """Track vision pipeline stage."""
    start = time.time()
    try:
        yield
    finally:
        VISION_DURATION.labels(stage=stage).observe(time.time() - start)


def track_biometric_verification(similarity_score: float, threshold: float):
    """Track biometric verification result."""
    BIOMETRIC_VERIFICATIONS_TOTAL.inc()
    BIOMETRIC_SIMILARITY.observe(similarity_score)

    if similarity_score >= threshold:
        BIOMETRIC_MATCHES_TOTAL.inc()
    else:
        BIOMETRIC_REJECTIONS_TOTAL.inc()


def track_blockchain_transaction(status: str, gas_used: int = 0):
    """Track blockchain transaction."""
    BLOCKCHAIN_TRANSACTIONS_TOTAL.labels(status=status).inc()
    if gas_used > 0:
        BLOCKCHAIN_GAS_USED.inc(gas_used)


def track_ipfs_pin(status: str, duration: float = 0):
    """Track IPFS pin operation."""
    IPFS_PINS_TOTAL.labels(status=status).inc()
    if duration > 0:
        IPFS_PIN_DURATION.observe(duration)


__all__ = [
    "PrometheusMiddleware",
    "metrics_endpoint",
    "init_app_info",
    "track_osint_engine",
    "track_vision_stage",
    "track_biometric_verification",
    "track_blockchain_transaction",
    "track_ipfs_pin",
    "HTTP_REQUESTS_TOTAL",
    "HTTP_REQUEST_DURATION",
    "OSINT_REQUESTS_TOTAL",
    "OSINT_SUCCESS_TOTAL",
    "BIOMETRIC_VERIFICATIONS_TOTAL",
    "BLOCKCHAIN_TRANSACTIONS_TOTAL",
    "IPFS_PINS_TOTAL",
]
