"""Conservative IR canonicalization and hard hashing."""

from __future__ import annotations

import hashlib
from pathlib import Path


NORMALIZER_VERSION = "hard-normalizer-v1"


def hard_canonicalize(ir_text: str) -> str:
    text = ir_text.replace("\r\n", "\n").replace("\r", "\n")
    if text.startswith("\ufeff"):
        text = text[1:]
    if not text.endswith("\n"):
        text += "\n"
    return text


def hard_hash_text(ir_text: str) -> str:
    canonical = hard_canonicalize(ir_text)
    return hashlib.sha256(
        canonical.encode("utf-8", errors="surrogateescape")
    ).hexdigest()


def hard_hash(ir_path: str | Path) -> str:
    path = Path(ir_path)
    text = path.read_bytes().decode("utf-8", errors="surrogateescape")
    return hard_hash_text(text)

