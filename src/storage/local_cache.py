import os
from pathlib import Path
from typing import Optional


class LocalArtifactCache:
    def __init__(self, cache_dir: Optional[str] = None):
        if cache_dir:
            self.base_dir = Path(cache_dir)
        else:
            self.base_dir = Path(".cache/traceface_artifacts")
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _get_path(self, key: str) -> Path:
        safe_key = "".join(c for c in key if c.isalnum() or c in ("-", "_", "."))
        return self.base_dir / safe_key

    def store(self, key: str, data: bytes) -> None:
        file_path = self._get_path(key)
        file_path.write_bytes(data)

    def retrieve(self, key: str) -> Optional[bytes]:
        file_path = self._get_path(key)
        if file_path.exists():
            return file_path.read_bytes()
        return None

    def exists(self, key: str) -> bool:
        return self._get_path(key).exists()
