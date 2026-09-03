import hashlib
import struct
from pathlib import Path

from Crypto.Hash import keccak


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(file_path: str | Path) -> str:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def keccak256_bytes(data: bytes) -> str:
    k = keccak.new(digest_bits=256)
    k.update(data)
    return "0x" + k.hexdigest()


def keccak256_hex(hex_str: str) -> str:
    clean_hex = hex_str.removeprefix("0x")
    raw_bytes = bytes.fromhex(clean_hex)
    return keccak256_bytes(raw_bytes)


def hash_face_embedding(vector: list[float]) -> str:
    # Deterministic IEEE 754 float32 big-endian byte serialization
    packed = struct.pack(f">{len(vector)}f", *vector)
    return keccak256_bytes(packed)
