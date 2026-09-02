import json
from typing import Any


def canonicalize_json(data: Any) -> bytes:
    """
    Serializes a Python dict/object into canonical JSON UTF-8 bytes
    following RFC 8785 (JSON Canonicalization Scheme).
    """
    try:
        import canonicaljson
        return canonicaljson.encode_canonical_json(data)
    except ImportError:
        # Strict deterministic fallback
        canonical_str = json.dumps(
            data,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":")
        )
        return canonical_str.encode("utf-8")


def canonicalize_and_hash(data: Any) -> str:
    from src.crypto.hasher import keccak256_bytes
    return keccak256_bytes(canonicalize_json(data))
