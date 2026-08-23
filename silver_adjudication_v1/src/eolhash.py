"""Newline-tolerant SHA-256 for text freeze verification.

Frozen manifests are not rewritten. Git autocrlf and mixed freeze-time
endings can change working-tree bytes without changing JSON records.
Verification accepts concat(parts) as raw, all-LF, all-CRLF, or with a
single file using the opposite ending (the Cursor resolver freeze).
"""
from __future__ import annotations

import hashlib
from pathlib import Path


def _lf(data: bytes) -> bytes:
    return data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def _crlf(data: bytes) -> bytes:
    return _lf(data).replace(b"\n", b"\r\n")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _concat(parts: list[bytes]) -> bytes:
    return b"".join(parts)


def digest_matches(expected: str, parts: list[bytes]) -> bool:
    """Return True if expected equals sha256 of parts under EOL folding."""
    if not expected or not parts:
        return False
    lf_parts = [_lf(p) for p in parts]
    crlf_parts = [_crlf(p) for p in parts]
    candidates = [
        _concat(parts),
        _concat(lf_parts),
        _concat(crlf_parts),
    ]
    for i in range(len(parts)):
        mixed_lf = list(crlf_parts)
        mixed_lf[i] = lf_parts[i]
        mixed_crlf = list(lf_parts)
        mixed_crlf[i] = crlf_parts[i]
        candidates.append(_concat(mixed_lf))
        candidates.append(_concat(mixed_crlf))
    return any(sha256_hex(c) == expected for c in candidates)


def path_digest_matches(expected: str, path: Path) -> bool:
    return digest_matches(expected, [path.read_bytes()])


def paths_digest_matches(expected: str, paths: list[Path]) -> bool:
    return digest_matches(expected, [p.read_bytes() for p in paths])
