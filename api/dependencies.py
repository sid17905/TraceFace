"""Shared singletons and FastAPI dependency providers.

The heavy deep-learning models (RetinaFace + ArcFace via InsightFace) are
expensive to construct, so :class:`VisionPipeline` is instantiated exactly once
and lazily — the first request that needs vision pays the load cost, and every
later request reuses the warm models. Blockchain / ZK helpers are cheap but are
memoized here too so the whole app shares one wiring point.

Everything is imported lazily inside the getters so that importing this module
(and therefore booting the ASGI app / generating OpenAPI docs) never triggers a
multi-second model load or a Web3 connection attempt.
"""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # pragma: no cover - typing only
    from src.blockchain.client import BlockchainClient
    from src.crypto.zk_prover import ZkBiometricProver
    from src.pipeline.orchestrator import VisionPipeline

# Module-level singletons, guarded by a lock so concurrent first-requests don't
# each kick off a redundant (and very expensive) model load.
_vision_pipeline: VisionPipeline | None = None
_vision_lock = threading.Lock()

_zk_prover: ZkBiometricProver | None = None


def get_vision_pipeline() -> VisionPipeline:
    """Return the process-wide :class:`VisionPipeline`, loading models on first use."""

    global _vision_pipeline
    if _vision_pipeline is None:
        with _vision_lock:
            if _vision_pipeline is None:
                from src.pipeline.orchestrator import VisionPipeline

                _vision_pipeline = VisionPipeline()
    return _vision_pipeline


def get_zk_prover() -> ZkBiometricProver:
    """Return the shared Groth16 biometric prover (cheap, no model load)."""

    global _zk_prover
    if _zk_prover is None:
        from src.crypto.zk_prover import ZkBiometricProver

        _zk_prover = ZkBiometricProver()
    return _zk_prover


def get_blockchain_client(private_key: str | None = None) -> BlockchainClient:
    """Construct a :class:`BlockchainClient`.

    Not memoized: a caller may need a client bound to a specific claimant private
    key (e.g. takedown submission). Construction is cheap and does not block on a
    live node — it degrades to simulated mode when disconnected.
    """

    from src.blockchain.client import BlockchainClient

    return BlockchainClient(private_key=private_key)


def warm_up() -> dict[str, Any]:
    """Eagerly load the vision models. Called from the app lifespan when enabled."""

    get_vision_pipeline()
    return {"vision": "loaded"}
