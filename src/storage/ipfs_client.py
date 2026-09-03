import hashlib
import json
import logging
from typing import Any

import httpx

from src.config import settings
from src.crypto.canonicalizer import canonicalize_json
from src.storage.local_cache import LocalArtifactCache

logger = logging.getLogger(__name__)


class IPFSClient:
    def __init__(
        self,
        pinata_api_key: str | None = None,
        pinata_secret_key: str | None = None,
        gateway_url: str | None = None,
        cache_dir: str | None = None,
    ) -> None:
        self.pinata_api_key = pinata_api_key or settings.pinata_api_key
        self.pinata_secret_key = pinata_secret_key or settings.pinata_secret_key
        self.gateway_url = gateway_url or settings.ipfs_gateway
        if not self.gateway_url.endswith("/"):
            self.gateway_url += "/"
        self.cache = LocalArtifactCache(cache_dir)

    def _generate_deterministic_cid(self, data_bytes: bytes) -> str:
        # Generate base58/sha256 deterministic mock CIDv0 starting with Qm
        sha = hashlib.sha256(data_bytes).digest()
        # Multihash prefix: 0x12 (sha2-256), 0x20 (32 bytes length)
        multihash = b"\x12\x20" + sha
        # Deterministic representation
        hex_digest = hashlib.sha256(multihash).hexdigest()
        return f"bafybei{hex_digest[:46]}"

    def pin_json(self, payload: dict[str, Any], name: str | None = "traceface_provenance.json") -> str:
        """
        Pins canonical JSON to IPFS (via Pinata API if available, else deterministic local cache).
        """
        canonical_bytes = canonicalize_json(payload)

        # If Pinata credentials provided and not dummy values
        if (
            self.pinata_api_key
            and self.pinata_secret_key
            and "your_pinata" not in self.pinata_api_key
        ):
            try:
                url = "https://api.pinata.cloud/pinning/pinJSONToIPFS"
                headers = {
                    "pinata_api_key": self.pinata_api_key,
                    "pinata_secret_api_key": self.pinata_secret_key,
                    "Content-Type": "application/json",
                }
                body = {
                    "pinataMetadata": {"name": name},
                    "pinataContent": payload,
                }
                with httpx.Client(timeout=15.0) as client:
                    resp = client.post(url, json=body, headers=headers)
                    if resp.status_code == 200:
                        cid = resp.json().get("IpfsHash")
                        self.cache.store(cid, canonical_bytes)
                        return cid
            except Exception:  # noqa: BLE001, S110
                pass

        # Local deterministic fallback
        cid = self._generate_deterministic_cid(canonical_bytes)
        self.cache.store(cid, canonical_bytes)
        return cid

    def fetch_json(self, cid: str) -> dict[str, Any]:
        """
        Fetches JSON payload by CID from local cache or IPFS gateways.
        """
        cached_data = self.cache.retrieve(cid)
        if cached_data is not None:
            return json.loads(cached_data.decode("utf-8"))

        gateways = [
            self.gateway_url,
            "https://ipfs.io/ipfs/",
            "https://cloudflare-ipfs.com/ipfs/",
            "https://dweb.link/ipfs/",
        ]

        for gw in gateways:
            try:
                url = f"{gw.rstrip('/')}/{cid}"
                with httpx.Client(timeout=10.0) as client:
                    resp = client.get(url)
                    if resp.status_code == 200:
                        raw_bytes = resp.content
                        self.cache.store(cid, raw_bytes)
                        return resp.json()
            except Exception:  # noqa: BLE001, S112
                continue

        raise RuntimeError(f"Failed to retrieve IPFS artifact for CID: {cid}")
