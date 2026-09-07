"""TraceFace FastAPI application package.

Exposes the biometric OSINT + Web3 provenance pipeline (``src/``) over an async
REST + Server-Sent-Events API. The core engines are synchronous and CPU-bound,
so blocking calls are offloaded to a threadpool via ``run_in_threadpool``.
"""

__all__ = ["__version__"]

__version__ = "1.0.0"
