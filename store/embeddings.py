"""Placeholder embedding function.

This is a deterministic, dependency-free hash-based embedding used so the
evidence store's pgvector column and similarity search are exercisable in
Foundations without pulling in a real embedding model. It has no semantic
meaning — swap `embed_text` for a call to a real embedding provider when one
is chosen; every caller goes through this one function, so that's the only
place that needs to change.
"""

import hashlib
import struct

EMBEDDING_DIM = 384


def embed_text(text: str) -> list[float]:
    vector: list[float] = []
    counter = 0
    while len(vector) < EMBEDDING_DIM:
        digest = hashlib.sha256(f"{text}:{counter}".encode()).digest()
        for i in range(0, len(digest) - 3, 4):
            if len(vector) >= EMBEDDING_DIM:
                break
            (as_int,) = struct.unpack(">I", digest[i : i + 4])
            vector.append((as_int / 0xFFFFFFFF) * 2 - 1)  # scale to [-1, 1]
        counter += 1
    return vector
