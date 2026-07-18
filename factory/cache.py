"""Content-hash cache for paid API calls.

The rule from hard experience: never pay twice for the same asset, and never
retry a paid call blindly. The hash covers everything that changes the output —
model, prompt, size, reference. Change any of them and you get a new asset.
Change nothing and you get the file already on disk, for free.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from . import config


def content_hash(**parts: object) -> str:
    """Stable hash of whatever defines an asset's identity."""
    payload = json.dumps(parts, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def cached_path(key: str, extension: str) -> Path:
    config.ensure_dirs()
    return config.ASSETS_DIR / f"{key}.{extension.lstrip('.')}"


def get(key: str, extension: str) -> Path | None:
    path = cached_path(key, extension)
    return path if path.exists() and path.stat().st_size > 0 else None


def put(key: str, extension: str, data: bytes) -> Path:
    path = cached_path(key, extension)
    path.write_bytes(data)
    return path
